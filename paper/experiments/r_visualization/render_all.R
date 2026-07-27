#!/usr/bin/env Rscript

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1]]), winslash = "/")
} else {
  normalizePath("paper/experiments/r_visualization/render_all.R", winslash = "/")
}
script_dir <- dirname(script_path)

scripts <- c(
  "render_method_framework.R",
  "plot_exp1.R",
  "plot_exp2.R",
  "plot_exp3_sensitivity.R",
  "plot_exp4.R"
)

for (script in scripts) {
  message("Rendering ", script)
  status <- system2(
    command = file.path(R.home("bin"), "Rscript.exe"),
    args = shQuote(file.path(script_dir, script))
  )
  if (!identical(status, 0L)) {
    stop("Figure rendering failed in ", script, " (exit ", status, ")")
  }
}

message("All current manuscript figures rendered successfully.")
