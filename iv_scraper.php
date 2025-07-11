<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);

require_once 'config.php';

// Connect to MySQL
$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Helper: Parse IV array from HTML
function parse_iv_array($html) {
    if (preg_match('/<div[^>]+id="tIVsCollapsible"[^>]*>(\[\[.*?\]\])<\/div>/s', $html, $matches)) {
        $array_str = $matches[1];
        // Extract triplets
        preg_match_all('/\[(\d{1,2}),\s*(\d{1,2}),\s*(\d{1,2})\]/', $array_str, $triplets, PREG_SET_ORDER);
        $ivs = [];
        foreach ($triplets as $t) {
            $ivs[] = [$t[1], $t[2], $t[3]];
        }
        return $ivs;
    }
    return [];
}

// URLs to fetch
$urls = [
    "https://pvpivs.com/searchStr.html?mon=Jangmo_O&cp=All&r=1-1-1-1_1-1-1-1_1-1-1-1_f_f&slMax=35", // base
    "https://pvpivs.com/searchStr.html?mon=Jangmo_O&cp=All&r=1-1-1-1_1-1-1-1_1-1-1-1_f_f&m=50&slMax=35" // best buddy
];

$sets = [];
$name = "Unknown";

foreach ($urls as $url) {
    $html = file_get_contents($url);
    if (!$html) {
        $sets[] = [];
        continue;
    }
    // Extract name from URL
    if (preg_match('/mon=([A-Za-z0-9_]+)/', $url, $m)) {
        $name = $m[1];
    }
    $ivs = parse_iv_array($html);
    $set = [];
    foreach ($ivs as $iv) {
        $set[implode(',', $iv)] = $iv; // Use string key for uniqueness
    }
    $sets[] = $set;
}

if (count($sets) < 2) {
    die("Not enough data.");
}

$base_set = $sets[0];
$buddy_set = $sets[1];

// IVs only in buddy_set need best buddy
$need_buddy = array_diff_key($buddy_set, $base_set);
// IVs in base_set (with or without buddy) do not need best buddy
$no_buddy = $base_set;

// Insert IVs that do NOT need best buddy
foreach ($no_buddy as $iv) {
    $attack = $iv[0];
    $defense = $iv[1];
    $hp = $iv[2];
    $sql = "INSERT IGNORE INTO pokemon (Name, Attack, Defense, Hp, NeedBestBuddy) VALUES (?, ?, ?, ?, 0)";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("siii", $name, $attack, $defense, $hp);
    $stmt->execute();
    $stmt->close();
}

// Insert IVs that DO need best buddy
foreach ($need_buddy as $iv) {
    $attack = $iv[0];
    $defense = $iv[1];
    $hp = $iv[2];
    $sql = "INSERT IGNORE INTO pokemon (Name, Attack, Defense, Hp, NeedBestBuddy) VALUES (?, ?, ?, ?, 1)";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("siii", $name, $attack, $defense, $hp);
    $stmt->execute();
    $stmt->close();
}

echo "Done!";

$conn->close();
?>