<?php
header('Content-Type: application/json');
echo json_encode([
    'status' => 'ok',
    'message' => 'PHP backend is working!',
    'timestamp' => date('Y-m-d H:i:s')
]);
