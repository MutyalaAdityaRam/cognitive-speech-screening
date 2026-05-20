<?php
require_once __DIR__ . '/../config/database.php';
header('Content-Type: application/json');
echo json_encode([
    'AI_SERVICE_URL' => getenv('AI_SERVICE_URL'),
    'MYSQL_HOST' => getenv('MYSQL_HOST'),
    'MYSQL_DATABASE' => getenv('MYSQL_DATABASE'),
    'loaded' => true
]);
