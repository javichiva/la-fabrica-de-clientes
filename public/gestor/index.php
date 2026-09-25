<?php
declare(strict_types=1);
require __DIR__.'/bootstrap.php';
config();
session_start_private();
$logged = authenticated();
$error = '';
$notice = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!csrf_ok()) { http_response_code(403); $error = 'La sesión del formulario ha caducado. Recarga la página e inténtalo de nuevo.'; }
    elseif (($_POST['action'] ?? '') === 'login') {
        if (!limit_request('login', 8, 900)) { http_response_code(429); $error = 'Demasiados intentos. Espera 15 minutos para volver a entrar.'; }
        else {
            $password = $_POST['password'] ?? '';
            $settings = config();
            if (is_string($password) && strlen($password) <= 1024 && hash_equals($settings['hash'], hash_pbkdf2('sha256', $password, $settings['salt'], (int)$settings['iterations'], 64))) {
                session_regenerate_id(true);
                $_SESSION = ['authenticated'=>$settings['hash'], 'csrf'=>bin2hex(random_bytes(32)), 'last'=>time(), 'started'=>time()];
                redirect('/gestor/');
            }
            http_response_code(401); $error = 'La contraseña no es correcta.';
        }
    } elseif (!$logged) { http_response_code(401); $error = 'Tu sesión ha caducado. Vuelve a entrar.'; }
    elseif (($_POST['action'] ?? '') === 'logout') { $_SESSION=[]; session_destroy(); setcookie(session_name(), '', ['expires'=>1,'path'=>'/gestor/','secure'=>PHP_SAPI !== 'cli-server','httponly'=>true,'samesite'=>'Strict']); redirect('/gestor/'); }
    elseif (in_array($_POST['action'] ?? '', ['save','delete'], true)) {
        try {
            $id = value('id', 24); $status = value('status', 30); $notes = value('notes', 20000);
            $version = filter_var($_POST['version'] ?? '', FILTER_VALIDATE_INT);
            if (!preg_match('/^[a-f0-9]{24}$/', $id) || !isset(statuses()[$status]) || $version === false) throw new InvalidArgumentException();
            $delete = $_POST['action'] === 'delete';
            if ($delete && ($_POST['confirm_delete'] ?? '') !== 'yes') throw new InvalidArgumentException();
            $result = database(function (&$db) use ($id, $status, $notes, $version, $delete): string {
                if (!isset($db['leads'][$id])) return 'missing';
                if ($db['leads'][$id]['version'] !== $version) return 'conflict';
                if ($delete) unset($db['leads'][$id]);
                else { $db['leads'][$id]['status']=$status; $db['leads'][$id]['notes']=$notes; $db['leads'][$id]['updated']=gmdate('c'); $db['leads'][$id]['version']++; }
                return 'ok';
            });
            if ($result === 'ok') { $_SESSION['notice'] = $delete ? 'Consulta eliminada.' : 'Cambios guardados.'; redirect('/gestor/'.($delete ? '' : '?id='.$id)); }
            http_response_code($result === 'missing' ? 404 : 409);
            $error = $result === 'missing' ? 'Esta consulta ya no existe.' : 'Esta ficha ha cambiado en otra pestaña. Copia tus notas antes de recargar para no perderlas.';
        } catch (InvalidArgumentException $e) { http_response_code(422); $error = 'Revisa los datos. Para eliminar una consulta debes marcar la confirmación.'; }
    }
}
$notice = (string)($_SESSION['notice'] ?? ''); unset($_SESSION['notice']);
$leads = $logged ? database(fn($db)=>$db['leads'], false) : [];
$id = is_string($_GET['id'] ?? null) ? $_GET['id'] : '';
$lead = $id !== '' ? ($leads[$id] ?? null) : null;
if ($logged && $id !== '' && !$lead) { http_response_code(404); $error='La consulta no existe o se ha eliminado.'; }
$q = is_string($_GET['q'] ?? null) ? substr(trim($_GET['q']),0,200) : '';
$filter = is_string($_GET['estado'] ?? null) && isset(statuses()[$_GET['estado']]) ? $_GET['estado'] : '';
$filtered = array_filter($leads, fn($l)=>($filter === '' || $l['status'] === $filter) && ($q === '' || stripos($l['nombre'].' '.$l['empresa'].' '.$l['email'].' '.$l['telefono'], $q) !== false));
uasort($filtered, fn($a,$b)=>strcmp($b['created'],$a['created']));
$pages = max(1,(int)ceil(count($filtered)/25));
$page = max(1,min($pages,(int)(is_scalar($_GET['pagina'] ?? null) ? $_GET['pagina'] : 1)));
$rows = array_slice($filtered,($page-1)*25,25);
function date_label(string $date): string { return date('d/m/Y · H:i', strtotime($date)); }
?>
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Gestor privado | La Fábrica de Clientes</title><link rel="stylesheet" href="/gestor/manager.css"><link rel="icon" href="/favicon.svg"></head><body>
<header class="top"><a class="brand" href="/gestor/">La Fábrica<span>de Clientes.</span></a><span class="private">GESTOR PRIVADO</span><?php if ($logged): ?><form method="post"><?=csrf()?><button class="quiet" name="action" value="logout">Cerrar sesión ↗</button></form><?php endif ?></header>
<main class="<?= $logged ? 'workspace' : 'login' ?>">
<?php if ($error): ?><div class="alert error" role="alert"><?=h($error)?></div><?php endif ?>
<?php if ($notice): ?><div class="alert" role="status"><?=h($notice)?></div><?php endif ?>
<?php if (!$logged): ?>
<section class="panel"><p class="eyebrow">TU ESPACIO DE TRABAJO</p><h1>Hola, Javier.</h1><p class="muted">Entra para revisar las consultas de tu web y seguir cada oportunidad.</p><form method="post" class="stack"><?=csrf()?><label>Contraseña<input type="password" name="password" autocomplete="current-password" required maxlength="1024" autofocus></label><button name="action" value="login">Entrar al gestor ↗</button></form><p class="help">Acceso reservado. La sesión se cierra tras una hora sin actividad.</p></section>
<?php elseif ($lead): ?>
<a class="back" href="/gestor/">← Volver a consultas</a><div class="heading"><div><p class="eyebrow">FICHA DE CONTACTO</p><h1><?=h($lead['empresa'])?></h1><p class="muted">Recibida el <?=h(date_label($lead['created']))?> · Formulario web</p></div><span class="badge <?=h($lead['status'])?>"><?=h(statuses()[$lead['status']])?></span></div>
<div class="detail-grid"><section class="panel"><h2>La consulta</h2><dl><dt>Nombre</dt><dd><?=h($lead['nombre'])?></dd><dt>Correo</dt><dd><a href="mailto:<?=h(rawurlencode($lead['email']))?>"><?=h($lead['email'])?></a></dd><dt>Teléfono</dt><dd><?=h($lead['telefono'] ?: 'No indicado')?></dd><dt>Web</dt><dd><?=h($lead['web'] ?: 'No indicada')?></dd><dt>Inversión prevista</dt><dd><?=h($lead['inversion'])?></dd></dl><h3>Qué necesita mejorar</h3><p class="message"><?=h($lead['objetivo'])?></p><div class="actions"><a class="button" href="mailto:<?=h(rawurlencode($lead['email']))?>">Responder por correo ↗</a><?php $phone=preg_replace('/[^0-9+]/','',$lead['telefono']); if ($phone && preg_match('/^\+?[0-9]{6,15}$/',$phone)): ?><a class="button secondary" href="tel:<?=h($phone)?>">Llamar ↗</a><?php endif ?></div></section>
<section class="panel"><h2>Tu seguimiento</h2><form method="post" class="stack"><?=csrf()?><input type="hidden" name="id" value="<?=h($lead['id'])?>"><input type="hidden" name="version" value="<?=h($lead['version'])?>"><label>Estado<select name="status"><?php foreach(statuses() as $key=>$label): ?><option value="<?=h($key)?>" <?=$lead['status']===$key?'selected':''?>><?=h($label)?></option><?php endforeach ?></select></label><label>Notas privadas<textarea name="notes" rows="10" maxlength="5000" placeholder="Qué habéis hablado, próximos pasos…"><?=h($error && isset($_POST['notes']) && is_string($_POST['notes']) ? $_POST['notes'] : $lead['notes'])?></textarea></label><button name="action" value="save">Guardar cambios</button><p class="help">Última actualización: <?=h(date_label($lead['updated']))?>. Estas notas solo aparecen en tu gestor.</p><details class="danger"><summary>Eliminar consulta</summary><p>Se borrarán el mensaje, los datos y las notas del gestor. No podrás recuperarlos desde aquí.</p><label class="checkbox"><input type="checkbox" name="confirm_delete" value="yes"> Confirmo que quiero eliminar esta consulta.</label><button class="delete" name="action" value="delete">Eliminar definitivamente</button></details></form></section></div>
<?php else: ?>
<div class="heading"><div><p class="eyebrow">MENSAJES QUE ABREN CONVERSACIONES</p><h1>Tus consultas.</h1><p class="muted">Todo lo que llega desde el formulario de tu web, en un solo lugar.</p></div><a class="button secondary" href="/gestor/">Actualizar ↻</a></div>
<div class="stats"><a href="/gestor/"><strong><?=count($leads)?></strong><span>Consultas totales</span></a><a href="/gestor/?estado=nuevo"><strong><?=count(array_filter($leads,fn($l)=>$l['status']==='nuevo'))?></strong><span>Pendientes de contactar</span></a><a href="/gestor/?estado=propuesta"><strong><?=count(array_filter($leads,fn($l)=>$l['status']==='propuesta'))?></strong><span>Propuestas enviadas</span></a></div>
<section class="panel inbox"><form method="get" class="filters"><label>Buscar contacto<input type="search" name="q" value="<?=h($q)?>" maxlength="200" placeholder="Empresa, nombre, correo o teléfono"></label><label>Estado<select name="estado"><option value="">Todos los estados</option><?php foreach(statuses() as $key=>$label): ?><option value="<?=h($key)?>" <?=$filter===$key?'selected':''?>><?=h($label)?></option><?php endforeach ?></select></label><button>Filtrar</button><a href="/gestor/">Limpiar</a></form>
<?php if (!$rows): ?><div class="empty"><span aria-hidden="true">↗</span><h2><?=$leads ? 'No hay coincidencias.' : 'Aquí empieza el seguimiento.'?></h2><p><?=$leads ? 'Prueba otro nombre o cambia el estado del filtro.' : 'Cuando alguien envíe el formulario de la web, verás aquí su consulta. Los correos y mensajes de WhatsApp se gestionan en sus propias aplicaciones.'?></p></div><?php else: ?><div class="table-wrap"><table><thead><tr><th>Empresa / contacto</th><th>Inversión</th><th>Recibida</th><th>Estado</th><th><span class="sr-only">Abrir</span></th></tr></thead><tbody><?php foreach($rows as $row): ?><tr><td><a class="company" href="/gestor/?id=<?=h($row['id'])?>"><?=h($row['empresa'])?></a><span class="muted sub"><?=h($row['nombre'])?> · <?=h($row['email'])?></span></td><td><?=h($row['inversion'])?></td><td class="date"><?=h(date_label($row['created']))?></td><td><span class="badge <?=h($row['status'])?>"><?=h(statuses()[$row['status']])?></span></td><td><a href="/gestor/?id=<?=h($row['id'])?>" aria-label="Ver consulta de <?=h($row['empresa'])?>">Ver ↗</a></td></tr><?php endforeach ?></tbody></table></div><nav class="pagination" aria-label="Páginas de consultas"><span><?=count($filtered)?> consultas · Página <?=$page?> de <?=$pages?></span><?php foreach (['Anterior'=>$page-1, 'Siguiente'=>$page+1] as $label=>$target): if ($target>=1 && $target<=$pages): ?><a href="?<?=h(http_build_query(['q'=>$q,'estado'=>$filter,'pagina'=>$target]))?>"><?=h($label)?></a><?php endif; endforeach ?></nav><?php endif ?></section>
<p class="help">Marca cada consulta como contactada después de responder. Los envíos se guardan aquí; no se envían avisos por correo en esta primera versión.</p>
<?php endif ?></main><footer class="bottom">La Fábrica de Clientes · Acceso privado <a href="/">Ver la web ↗</a></footer></body></html>
