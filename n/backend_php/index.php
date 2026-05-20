<?php
declare(strict_types=1);

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

echo json_encode([
    'service' => 'speech_project PHP API Gateway',
    'status' => 'ok',
    'api_base' => 'http://10.78.191.50/speech_project/api',
    'python_ai_service' => getenv('AI_SERVICE_URL') ?: 'http://10.78.191.50:8000',
]);
