<?php
declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

function ai_service_url(): string
{
    return rtrim(getenv('AI_SERVICE_URL') ?: 'http://10.78.191.50:8000', '/');
}
