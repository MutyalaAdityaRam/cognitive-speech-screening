<?php
declare(strict_types=1);

function report_storage_dir(): string
{
    $dir = __DIR__ . '/../storage/reports/';
    if (!is_dir($dir)) {
        mkdir($dir, 0777, true);
    }
    return $dir;
}

function report_body(array $aiResult): string
{
    $timestamp = gmdate('c');
    $risk = (string)($aiResult['risk_level'] ?? $aiResult['prediction'] ?? 'Unknown');
    $confidence = (string)($aiResult['confidence'] ?? $aiResult['final_probability'] ?? '0');
    $summary = summarize_text((string)($aiResult['transcript'] ?? ''));
    $reportText = (string)($aiResult['final_report'] ?? $aiResult['report_text'] ?? '');
    return "Generated: {$timestamp}\nRisk Level: {$risk}\nConfidence: {$confidence}\n\nTranscript Summary\n{$summary}\n\n{$reportText}";
}

function save_report_files(int $sessionId, array $aiResult): array
{
    $base = report_storage_dir() . 'session_' . $sessionId . '_' . time();
    $body = report_body($aiResult);
    $txt = $base . '.txt';
    $pdf = $base . '.pdf';
    $docx = $base . '.docx';
    file_put_contents($txt, $body);
    try {
        write_simple_pdf($pdf, $body);
    } catch (Throwable $e) {
        error_log('PDF report artifact failed: ' . $e->getMessage());
    }
    try {
        write_simple_docx($docx, $body);
    } catch (Throwable $e) {
        error_log('DOCX report artifact failed: ' . $e->getMessage());
    }
    return ['pdf' => $pdf, 'docx' => $docx, 'txt' => $txt];
}

function save_selected_report_file(int $reportId, string $format, array $data): string
{
    $format = strtolower($format);
    if (!in_array($format, ['pdf', 'doc', 'docx'], true)) {
        throw new InvalidArgumentException('Unsupported report format');
    }

    $base = report_storage_dir() . 'report_' . $reportId . '_' . time();
    $path = $base . '.' . ($format === 'docx' ? 'docx' : $format);
    $body = report_body($data);

    if ($format === 'pdf') {
        write_simple_pdf($path, $body);
        return $path;
    }

    if ($format === 'doc') {
        write_simple_word_doc($path, $body);
        return $path;
    }

    write_simple_docx($path, $body);
    if (!is_file($path) && is_file($path . '.txt')) {
        return $path . '.txt';
    }
    return $path;
}

function summarize_text(string $text, int $maxWords = 45): string
{
    $words = preg_split('/\s+/', trim($text));
    if (!$words || $words[0] === '') {
        return 'Transcript summary unavailable.';
    }
    $slice = array_slice($words, 0, $maxWords);
    return implode(' ', $slice) . (count($words) > $maxWords ? '...' : '');
}

function write_simple_docx(string $path, string $text): void
{
    if (!class_exists('ZipArchive')) {
        file_put_contents($path . '.txt', $text);
        return;
    }
    $paragraphs = '';
    foreach (preg_split('/\R/', $text) as $line) {
        $paragraphs .= '<w:p><w:r><w:t>' . htmlspecialchars($line, ENT_XML1 | ENT_COMPAT, 'UTF-8') . '</w:t></w:r></w:p>';
    }
    $document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        . '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        . $paragraphs . '</w:body></w:document>';
    $zip = new ZipArchive();
    $zip->open($path, ZipArchive::CREATE | ZipArchive::OVERWRITE);
    $zip->addFromString('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>');
    $zip->addFromString('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>');
    $zip->addFromString('word/document.xml', $document);
    $zip->close();
}

function write_simple_word_doc(string $path, string $text): void
{
    $escaped = nl2br(htmlspecialchars($text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'));
    $html = '<!doctype html><html><head><meta charset="utf-8"><title>Cognitive Screening Report</title></head><body style="font-family:Arial,sans-serif;line-height:1.45;">' . $escaped . '</body></html>';
    file_put_contents($path, $html);
}

function write_simple_pdf(string $path, string $text): void
{
    $lines = [];
    foreach (preg_split('/\R/', $text) as $raw) {
        $wrapped = str_split($raw, 88);
        $lines = array_merge($lines, $wrapped ?: ['']);
    }
    $stream = "BT\n/F1 10 Tf\n50 750 Td\n14 TL\n";
    foreach (array_slice($lines, 0, 45) as $line) {
        $safe = str_replace(['\\', '(', ')'], ['\\\\', '\\(', '\\)'], $line);
        $stream .= "({$safe}) Tj\nT*\n";
    }
    $stream .= "ET";
    $objects = [
        '<< /Type /Catalog /Pages 2 0 R >>',
        '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>',
        '<< /Length ' . strlen($stream) . " >>\nstream\n{$stream}\nendstream",
    ];
    $pdf = "%PDF-1.4\n";
    $offsets = [0];
    foreach ($objects as $i => $object) {
        $offsets[] = strlen($pdf);
        $pdf .= ($i + 1) . " 0 obj\n{$object}\nendobj\n";
    }
    $xref = strlen($pdf);
    $pdf .= "xref\n0 5\n0000000000 65535 f \n";
    for ($i = 1; $i <= 4; $i++) {
        $pdf .= sprintf("%010d 00000 n \n", $offsets[$i]);
    }
    $pdf .= "trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{$xref}\n%%EOF";
    file_put_contents($path, $pdf);
}
