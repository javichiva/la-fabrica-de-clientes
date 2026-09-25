<?php
declare(strict_types=1);
// Shared implementation; no output and no public configuration endpoint.
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Madrid');
header('Cache-Control: no-store, private');
header('X-Robots-Tag: noindex, nofollow');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');
header('X-Frame-Options: DENY');
header("Content-Security-Policy: default-src 'none'; style-src 'self'; img-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'");
set_exception_handler(function (Throwable $e): void {
    // Never write contact details, passwords or request payloads to the server log.
    error_log('Fabrica manager: internal operation failed ('.get_class($e).').');
    http_response_code(503);
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><html lang="es"><meta charset="utf-8"><title>Servicio temporalmente no disponible</title><p>No se ha podido completar la operación. Inténtalo más tarde o escribe a info@javierchiva.com.</p></html>';
});

function config(): array {
    static $config;
    if ($config === null) {
        $file = dirname(__DIR__).'/_fabrica-private/auth.json';
        $config = json_decode((string)file_get_contents($file), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($config) || !isset($config['hash'], $config['salt'], $config['iterations']) || strlen($config['hash']) !== 64) {
            throw new RuntimeException('Configuration unavailable');
        }
    }
    return $config;
}

function storage_path(): string {
    // Outside public_html; releases and FTP cutovers cannot replace customer records.
    $path = dirname(__DIR__, 2).'/.fabrica-manager';
    if (!is_dir($path) && !mkdir($path, 0700, true) && !is_dir($path)) {
        throw new RuntimeException('Storage unavailable');
    }
    return $path;
}

function database(callable $operation, bool $write = true) {
    $path = storage_path();
    $lock = fopen($path.'/store.lock', 'c');
    if (!$lock || !flock($lock, $write ? LOCK_EX : LOCK_SH)) throw new RuntimeException('Lock unavailable');
    try {
        $file = $path.'/store.json';
        $data = is_file($file) ? json_decode((string)file_get_contents($file), true, 512, JSON_THROW_ON_ERROR) : ['leads'=>[], 'limits'=>[]];
        if (!isset($data['leads'], $data['limits'])) throw new RuntimeException('Invalid storage');
        $result = $operation($data);
        if ($write) {
            $tmp = tempnam($path, '.write-');
            if ($tmp === false) throw new RuntimeException('Write unavailable');
            try {
                chmod($tmp, 0600);
                $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
                if (file_put_contents($tmp, $json) !== strlen($json) || !rename($tmp, $file)) throw new RuntimeException('Write failed');
            } finally { if (is_file($tmp)) unlink($tmp); }
        }
        return $result;
    } finally { flock($lock, LOCK_UN); fclose($lock); }
}

function limit_request(string $scope, int $max, int $seconds): bool {
    // Retain only a keyed hash of the remote address, never the address itself.
    $key = $scope.':'.hash_hmac('sha256', (string)($_SERVER['REMOTE_ADDR'] ?? ''), config()['salt']);
    return database(function (&$db) use ($key, $max, $seconds): bool {
        $now = time();
        foreach ($db['limits'] as $k=>$v) if ($v['until'] <= $now) unset($db['limits'][$k]);
        if (!isset($db['limits'][$key])) {
            if (count($db['limits']) >= 20000) return false;
            $db['limits'][$key] = ['until'=>$now+$seconds, 'count'=>0];
        }
        return ++$db['limits'][$key]['count'] <= $max;
    });
}

function value(string $key, int $max): string {
    $value = $_POST[$key] ?? '';
    if (!is_string($value) || strlen($value) > $max || preg_match('//u', $value) !== 1 || str_contains($value, "\0")) {
        throw new InvalidArgumentException('Invalid field');
    }
    return trim($value);
}
function h($text): string { return htmlspecialchars((string)$text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function origin_ok(): bool {
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    $expected = 'https://www.lafabricadeclientes.es';
    if (PHP_SAPI === 'cli-server') $expected = 'http://'.($_SERVER['HTTP_HOST'] ?? 'localhost');
    return ($origin === '' || $origin === $expected) && ($_SERVER['HTTP_SEC_FETCH_SITE'] ?? '') !== 'cross-site';
}
function session_start_private(): void {
    session_name('fabrica_manager');
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    session_save_path(storage_path());
    session_set_cookie_params(['lifetime'=>0, 'path'=>'/gestor/', 'secure'=>PHP_SAPI !== 'cli-server', 'httponly'=>true, 'samesite'=>'Strict']);
    session_cache_limiter('');
    session_start();
    if (!isset($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
}
function csrf(): string { return '<input type="hidden" name="csrf" value="'.h($_SESSION['csrf']).'">'; }
function csrf_ok(): bool { return origin_ok() && is_string($_POST['csrf'] ?? null) && hash_equals($_SESSION['csrf'], $_POST['csrf']); }
function authenticated(): bool {
    $ok = isset($_SESSION['authenticated'], $_SESSION['last'], $_SESSION['started'])
        && hash_equals(config()['hash'], (string)$_SESSION['authenticated'])
        && time()-$_SESSION['last'] < 3600 && time()-$_SESSION['started'] < 28800;
    if ($ok) $_SESSION['last'] = time();
    return $ok;
}
function redirect(string $url): never { header('Location: '.$url, true, 303); exit; }
function statuses(): array { return ['nuevo'=>'Nuevo', 'contactado'=>'Contactado', 'propuesta'=>'Propuesta enviada', 'ganado'=>'Ganado', 'descartado'=>'No encaja']; }
