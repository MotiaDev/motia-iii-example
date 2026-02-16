//! Version comparison for CLI and template compatibility

use anyhow::Result;
use semver::Version;

/// Compare CLI version against template version
/// Returns a warning message if the CLI is older than the template expects
pub fn check_compatibility(
    cli_version: &str,
    template_version: &str,
    upgrade_command: &str,
) -> Option<String> {
    let cli_ver = match Version::parse(cli_version) {
        Ok(v) => v,
        Err(_) => return None, // Can't compare, skip warning
    };

    let template_ver = match Version::parse(template_version) {
        Ok(v) => v,
        Err(_) => return None, // Can't compare, skip warning
    };

    if cli_ver < template_ver {
        Some(format!(
            "Warning: This template was designed for CLI version {} or newer.\n\
             You are running version {}.\n\
             Consider updating: {}",
            template_version, cli_version, upgrade_command
        ))
    } else {
        None
    }
}

/// Parse version string, handling various formats
#[allow(dead_code)]
pub fn parse_version(version_str: &str) -> Result<Version> {
    // Remove leading 'v' if present
    let cleaned = version_str.strip_prefix('v').unwrap_or(version_str);
    Version::parse(cleaned).map_err(|e| anyhow::anyhow!("Invalid version '{}': {}", version_str, e))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cli_older_than_template() {
        let warning = check_compatibility("0.1.0", "0.2.0", "cargo install test-cli --force");
        assert!(warning.is_some());
        assert!(warning.unwrap().contains("0.2.0"));
    }

    #[test]
    fn test_cli_same_as_template() {
        let warning = check_compatibility("0.1.0", "0.1.0", "cargo install test-cli --force");
        assert!(warning.is_none());
    }

    #[test]
    fn test_cli_newer_than_template() {
        let warning = check_compatibility("0.2.0", "0.1.0", "cargo install test-cli --force");
        assert!(warning.is_none());
    }

    #[test]
    fn test_invalid_versions() {
        // Should return None (no warning) for invalid versions
        let warning = check_compatibility("invalid", "0.1.0", "cargo install test-cli --force");
        assert!(warning.is_none());
    }
}
