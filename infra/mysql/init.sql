-- ==============================================================================
-- DIGITAL DOCTOR MYSQL INITIALIZATION SCRIPT
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS `digital_doctor`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Ensure privileges for the application user
GRANT ALL PRIVILEGES ON `digital_doctor`.* TO 'digital_doctor_app'@'%';
FLUSH PRIVILEGES;
