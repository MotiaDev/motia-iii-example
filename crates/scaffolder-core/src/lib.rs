//! Scaffolder Core - Shared library for project scaffolding CLIs
//!
//! This library provides the core functionality for scaffolding projects from templates.
//! It is designed to be used by multiple CLI binaries (e.g., `motia`, `iii`) that share
//! the same underlying scaffolding logic but have different product configurations.
//!
//! # Architecture
//!
//! The library is organized into layers:
//!
//! - **Layer 1: Core Operations** - Pure functions for template fetching, copying, runtime detection
//! - **Layer 2: Workflow Orchestration** - `ProductConfig` trait and `ProjectBuilder` for custom UIs
//! - **Layer 3: CLI/TUI Interface** - Optional cliclack-based prompts (feature-gated)
//!
//! # Feature Flags
//!
//! - `tui` (default): Enables the cliclack-based TUI prompts module
//!
//! # Example Usage (without TUI)
//!
//! ```ignore
//! use scaffolder_core::{ProductConfig, templates, runtime};
//!
//! // Define your product config
//! #[derive(Clone)]
//! struct MyConfig;
//! impl ProductConfig for MyConfig {
//!     fn name(&self) -> &'static str { "myapp" }
//!     // ... implement other methods
//! }
//!
//! // Use the low-level APIs
//! let fetcher = templates::TemplateFetcher::from_config(&MyConfig)?;
//! let manifest = fetcher.fetch_root_manifest().await?;
//! ```

pub mod config;
pub mod product;
pub mod runtime;
pub mod templates;

#[cfg(feature = "tui")]
pub mod tui;

// Re-export main types for convenience
pub use product::ProductConfig;
pub use runtime::{check_runtimes, Language, RuntimeInfo};
pub use templates::{
    copy_template, LanguageFiles, RootManifest, TemplateFetcher, TemplateManifest, TemplateSource,
};

#[cfg(feature = "tui")]
pub use tui::run;

/// CLI version - used for template compatibility checking
/// Each binary should define its own version, but this provides a fallback
pub const DEFAULT_CLI_VERSION: &str = "0.1.0";
