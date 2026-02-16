//! Motia CLI - Project scaffolding for Motia workflows

use anyhow::Result;
use clap::{Parser, Subcommand};
use scaffolder_core::runtime::Language;
use scaffolder_core::tui::CreateArgs;
use scaffolder_core::ProductConfig;
use std::path::{Path, PathBuf};

/// CLI version
pub const CLI_VERSION: &str = env!("CARGO_PKG_VERSION");

/// Motia product configuration
#[derive(Clone)]
pub struct MotiaConfig;

impl ProductConfig for MotiaConfig {
    fn name(&self) -> &'static str {
        "motia"
    }

    fn display_name(&self) -> &'static str {
        "Motia"
    }

    fn default_template_url(&self) -> &'static str {
        "https://raw.githubusercontent.com/iii-hq/cli-tooling/main/templates/motia"
    }

    fn template_url_env(&self) -> &'static str {
        "MOTIA_TEMPLATE_URL"
    }

    fn requires_iii(&self) -> bool {
        true
    }

    fn docs_url(&self) -> &'static str {
        "https://motia.dev/docs"
    }

    fn cli_description(&self) -> &'static str {
        "CLI for scaffolding Motia projects with iii integration"
    }

    fn upgrade_command(&self) -> &'static str {
        "cargo install motia-tools --force"
    }

    fn next_steps(&self, dir: &Path, langs: &[Language]) -> Vec<String> {
        let mut steps = Vec::new();
        let current = std::env::current_dir().ok();

        let has_js_ts = langs
            .iter()
            .any(|l| matches!(l, Language::TypeScript | Language::JavaScript));
        let has_python = langs.contains(&Language::Python);

        // Step 1: Run iii
        steps.push("iii -c iii.config.yaml".to_string());

        // Step 2: cd to directory if not current
        if current.as_ref() != Some(&dir.to_path_buf()) {
            steps.push(format!("cd {}", dir.display()));
        }

        // Step 3: Install Node dependencies
        if has_js_ts {
            steps.push("npm install @iii-dev/motia".to_string());
        }

        // Step 4: Set up Python environment
        if has_python {
            steps.push(
                "Set up Python environment:\n\
                      uv venv && uv pip install -r requirements.txt\n\
                      -- or --\n\
                      python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
                    .to_string(),
            );
        }

        // Step 5: Start dev server
        if has_js_ts {
            steps.push("npm dev".to_string());
        }

        steps
    }
}

#[derive(Parser, Debug)]
#[command(name = "motia-tools")]
#[command(about = "CLI for scaffolding Motia projects with iii integration")]
#[command(version)]
pub struct Args {
    #[command(subcommand)]
    pub command: Option<Command>,
}

#[derive(Subcommand, Debug)]
pub enum Command {
    /// Create a new Motia project
    Create(CliCreateArgs),
    /// Build zip files for all templates in the template directory (for development use)
    BuildZips(BuildZipsArgs),
}

#[derive(Parser, Debug)]
pub struct CliCreateArgs {
    /// Local directory to use for templates instead of fetching from remote (for development use)
    #[arg(long = "template-dir")]
    pub template_dir: Option<PathBuf>,

    /// Template name to use
    #[arg(short, long)]
    pub template: Option<String>,

    /// Project directory to create
    #[arg(short, long)]
    pub directory: Option<PathBuf>,

    /// Languages to include (comma-separated: ts,js,py or typescript,javascript,python)
    #[arg(short, long, value_delimiter = ',')]
    pub languages: Option<Vec<String>>,

    /// Skip iii installation check
    #[arg(long = "skip-iii")]
    pub skip_iii: bool,

    /// Auto-confirm all prompts (non-interactive mode)
    #[arg(short, long)]
    pub yes: bool,
}

impl From<CliCreateArgs> for CreateArgs {
    fn from(args: CliCreateArgs) -> Self {
        CreateArgs {
            template_dir: args.template_dir,
            template: args.template,
            directory: args.directory,
            languages: args.languages,
            skip_tool_check: args.skip_iii,
            yes: args.yes,
        }
    }
}

#[derive(Parser, Debug)]
pub struct BuildZipsArgs {
    /// Local directory containing templates to build zips from (for development use)
    #[arg(long = "template-dir")]
    pub template_dir: Option<PathBuf>,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Ensure terminal cursor is restored on panic
    let default_panic = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let _ = console::Term::stderr().show_cursor();
        default_panic(info);
    }));

    // Handle Ctrl+C gracefully
    ctrlc::set_handler(move || {
        let _ = console::Term::stderr().show_cursor();
        std::process::exit(130);
    })
    .ok();

    let args = Args::parse();
    let config = MotiaConfig;

    // Handle subcommands
    match args.command {
        Some(Command::Create(create_args)) => {
            // Run the TUI application with the create args
            let result = scaffolder_core::run(&config, create_args.into(), CLI_VERSION).await;

            // Ensure cursor is visible on normal exit
            let _ = console::Term::stderr().show_cursor();

            result
        }
        Some(Command::BuildZips(build_args)) => {
            // Build zip files for templates
            scaffolder_core::templates::build_zips(&config, &build_args.template_dir).await
        }
        None => {
            // No subcommand provided, default to create behavior (interactive mode)
            let create_args = CreateArgs::default();
            let result = scaffolder_core::run(&config, create_args, CLI_VERSION).await;

            // Ensure cursor is visible on normal exit
            let _ = console::Term::stderr().show_cursor();

            result
        }
    }
}
