-- Runs automatically on first MySQL container startup (empty volume).
USE urlshortener;

CREATE TABLE IF NOT EXISTS urls (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    short_code   VARCHAR(16)     NOT NULL,
    original_url TEXT            NOT NULL,
    created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at   TIMESTAMP       NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_short_code (short_code),
    KEY idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
