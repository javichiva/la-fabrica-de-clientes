<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
function respond(int $status, string $message): never {
    http_response_code($status);
    if (str_contains($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json')) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(['ok'=>$status === 201, 'message'=>$message], JSON_UNESCAPED_UNICODE);
    } else {
        header('Content-Type: text/html; charset=utf-8');
        echo '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Tu consulta | La Fábrica de Clientes</title><link rel="stylesheet" href="/gestor/manager.css"></head><body><main class="login panel"><p class="eyebrow">LA FÁBRICA DE CLIENTES</p><h1>'.($status === 201 ? 'Consulta recibida.' : 'Revisa tu consulta.').'</h1><p>'.h($message).'</p><a href="/contacto/">Volver a contacto</a></main></body></html>';
    }
    exit;
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { header('Allow: POST'); respond(405, 'Utiliza el formulario de contacto.'); }
if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 20000) respond(413, 'La consulta es demasiado larga.');
if (!origin_ok()) respond(403, 'Envía la consulta desde el formulario de nuestra web.');
if (!limit_request('contact', 5, 3600)) { header('Retry-After: 3600'); respond(429, 'Has enviado varias consultas. Espera una hora o escríbenos a info@javierchiva.com.'); }
try {
    if (value('direccion_fax', 500) !== '') respond(400, 'No hemos podido validar el envío. Contacta por correo o teléfono.');
    $lead = [];
    foreach (['nombre'=>400, 'empresa'=>600, 'email'=>254, 'telefono'=>80, 'web'=>800, 'inversion'=>100, 'objetivo'=>12000] as $key=>$max) $lead[$key] = value($key, $max);
    if ($lead['nombre'] === '' || $lead['empresa'] === '' || !filter_var($lead['email'], FILTER_VALIDATE_EMAIL) || strlen($lead['objetivo']) < 20 || !in_array($lead['inversion'], ['Entre 10.000 y 20.000 €','Entre 20.000 y 40.000 €','Más de 40.000 €'], true)) {
        respond(422, 'Completa tu nombre, empresa, un correo válido, la inversión y un objetivo de al menos 20 caracteres.');
    }
} catch (InvalidArgumentException $e) { respond(422, 'Revisa los datos y la longitud de los campos.'); }
$lead += ['id'=>bin2hex(random_bytes(12)), 'created'=>gmdate('c'), 'status'=>'nuevo', 'notes'=>'', 'updated'=>gmdate('c'), 'version'=>1, 'source'=>'Formulario web'];
database(function (&$db) use ($lead): void {
    // Idempotence for browser retries without retaining an extra tracking identifier.
    foreach ($db['leads'] as $existing) {
        if (strtotime($existing['created']) > time()-600 && $existing['email'] === $lead['email'] && $existing['objetivo'] === $lead['objetivo'] && $existing['empresa'] === $lead['empresa']) return;
    }
    if (count($db['leads']) >= 10000) throw new RuntimeException('Inbox capacity');
    $db['leads'][$lead['id']] = $lead;
});
respond(201, 'Gracias. Hemos recibido tu consulta y la revisaremos para contactar contigo.');
