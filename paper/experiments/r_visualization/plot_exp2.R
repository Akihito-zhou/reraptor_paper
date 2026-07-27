#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(ggrepel)
  library(jsonlite)
  library(patchwork)
  library(scales)
})

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1]]), winslash = "/")
} else {
  normalizePath("paper/experiments/r_visualization/plot_exp2.R", winslash = "/")
}
script_dir <- dirname(script_path)
source(file.path(script_dir, "paper_theme.R"))
repo_root <- normalizePath(file.path(script_dir, "../../.."), winslash = "/")

args <- commandArgs(trailingOnly = TRUE)
input_flag <- grep("^--input=", args, value = TRUE)
if (length(input_flag)) {
  input_path <- normalizePath(
    sub("^--input=", "", input_flag[[1]]),
    winslash = "/",
    mustWork = TRUE
  )
} else {
  canonical_candidates <- Sys.glob(file.path(
    repo_root,
    "paper/results/exp2_ablation_study",
    "exp2_results_canonical_final*.json"
  ))
  if (!length(canonical_candidates)) {
    stop(
      "No merged canonical Exp2 result found. Pass ",
      "--input=<path> after all eight ablation shards are frozen."
    )
  }
  input_path <- canonical_candidates[[which.max(file.info(canonical_candidates)$mtime)]]
}

figure_dir <- file.path(repo_root, "paper/figures/exp2")
payload <- jsonlite::fromJSON(input_path, simplifyDataFrame = TRUE)
raw <- if (is.data.frame(payload)) payload else payload$results

required_columns <- c(
  "algorithm", "origin_name", "depart_time", "budget_minutes",
  "seed", "score_seed", "elapsed_ms", "stop_score_total", "labels",
  "resource_cap_hit", "termination_reason", "candidate_trim_events",
  "beam_trim_events"
)
if (!"origin_name" %in% names(raw) && "origin" %in% names(raw)) {
  raw$origin_name <- raw$origin
}
missing_columns <- setdiff(required_columns, names(raw))
if (length(missing_columns)) {
  stop("Missing Exp2 columns: ", paste(missing_columns, collapse = ", "))
}

config_labels <- c(
  "Ours (Full)" = "Full",
  "Ours (NoNeg)" = "- Negative",
  "Ours (NoDom)" = "- Dominance",
  "Ours (NoBeam)" = "- Beam",
  "Ours (NoBeam-NoDom)" = "- Beam - Dominance",
  "Ours (NoDom-NoNeg)" = "- Dominance - Negative",
  "Ours (NoBeam-NoNeg)" = "- Beam - Negative",
  "Ours (NoBeam-NoDom-NoNeg)" = "No search controls"
)

task <- raw %>%
  mutate(
    config = unname(config_labels[algorithm]),
    config = if_else(is.na(config), algorithm, config),
    stop_score_total = as.numeric(stop_score_total),
    elapsed_ms = as.numeric(elapsed_ms),
    labels = as.numeric(labels),
    resource_cap_hit = as.logical(resource_cap_hit),
    candidate_trim_events = as.numeric(candidate_trim_events),
    beam_trim_events = as.numeric(beam_trim_events)
  ) %>%
  group_by(
    algorithm, config, origin_name, depart_time,
    budget_minutes, seed, score_seed
  ) %>%
  summarise(
    stop_score = mean(stop_score_total, na.rm = TRUE),
    elapsed_ms = mean(elapsed_ms, na.rm = TRUE),
    labels = mean(labels, na.rm = TRUE),
    cap_hit = mean(as.numeric(resource_cap_hit), na.rm = TRUE),
    timeout = mean(termination_reason == "timeout", na.rm = TRUE),
    label_cap = mean(termination_reason == "label_cap", na.rm = TRUE),
    candidate_trim_active = mean(candidate_trim_events > 0, na.rm = TRUE),
    beam_trim_active = mean(beam_trim_events > 0, na.rm = TRUE),
    .groups = "drop"
  )

summary <- task %>%
  group_by(algorithm, config) %>%
  summarise(
    stop_score = mean(stop_score),
    elapsed_ms = mean(elapsed_ms),
    labels = mean(labels),
    cap_hit_rate = mean(cap_hit),
    timeout_rate = mean(timeout),
    label_cap_rate = mean(label_cap),
    candidate_trim_activation = mean(candidate_trim_active),
    beam_trim_activation = mean(beam_trim_active),
    task_count = dplyr::n(),
    .groups = "drop"
  )

full <- summary %>% filter(algorithm == "Ours (Full)")
if (nrow(full) != 1) {
  stop("Exp2 input must contain exactly one Full configuration summary.")
}

summary <- summary %>%
  mutate(
    score_delta = stop_score - full$stop_score,
    runtime_ratio = elapsed_ms / full$elapsed_ms,
    label_ratio = labels / full$labels,
    cap_hit_pct = 100 * cap_hit_rate,
    config = factor(
      config,
      levels = rev(c(
        "Full",
        "- Negative",
        "- Dominance",
        "- Beam",
        "- Dominance - Negative",
        "- Beam - Negative",
        "- Beam - Dominance",
        "No search controls"
      ))
    ),
    focal = config == "Full",
    point_color = if_else(focal, paper_colors$ours, paper_colors$baseline_dark)
  )

if (nrow(summary) != length(config_labels) || any(summary$task_count != 600)) {
  stop(
    "Exp2 canonical input must contain eight configurations with 600 tasks each."
  )
}

full_task <- task %>%
  filter(algorithm == "Ours (Full)") %>%
  select(
    origin_name, depart_time, budget_minutes, seed, score_seed,
    full_stop_score = stop_score
  )

paired_summary <- task %>%
  left_join(
    full_task,
    by = c(
      "origin_name", "depart_time", "budget_minutes", "seed", "score_seed"
    )
  ) %>%
  mutate(score_delta_vs_full = stop_score - full_stop_score) %>%
  group_by(algorithm, config) %>%
  summarise(
    paired_tasks = dplyr::n(),
    mean_score_delta_vs_full = mean(score_delta_vs_full),
    wins_vs_full = sum(score_delta_vs_full > 0),
    ties_vs_full = sum(score_delta_vs_full == 0),
    losses_vs_full = sum(score_delta_vs_full < 0),
    .groups = "drop"
  )

budget_summary <- task %>%
  group_by(algorithm, config, budget_minutes) %>%
  summarise(
    task_count = dplyr::n(),
    stop_score = mean(stop_score),
    elapsed_ms = mean(elapsed_ms),
    labels = mean(labels),
    cap_hit_rate = mean(cap_hit),
    timeout_rate = mean(timeout),
    label_cap_rate = mean(label_cap),
    .groups = "drop"
  )

summary_export <- summary %>%
  mutate(config = as.character(config)) %>%
  arrange(match(algorithm, names(config_labels)))
paired_export <- paired_summary %>%
  mutate(config = as.character(config)) %>%
  arrange(match(algorithm, names(config_labels)))
budget_export <- budget_summary %>%
  mutate(config = as.character(config)) %>%
  arrange(match(algorithm, names(config_labels)), budget_minutes)

result_dir <- file.path(repo_root, "paper/results/exp2_ablation_study")
utils::write.csv(
  summary_export,
  file.path(result_dir, "exp2_canonical_summary_20260725.csv"),
  row.names = FALSE
)
utils::write.csv(
  paired_export,
  file.path(result_dir, "exp2_canonical_paired_vs_full_20260725.csv"),
  row.names = FALSE
)
utils::write.csv(
  budget_export,
  file.path(result_dir, "exp2_canonical_by_budget_20260725.csv"),
  row.names = FALSE
)
jsonlite::write_json(
  list(
    source = input_path,
    generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
    overall = summary_export,
    paired_vs_full = paired_export,
    by_budget = budget_export
  ),
  file.path(result_dir, "exp2_canonical_analysis_20260725.json"),
  dataframe = "rows",
  pretty = TRUE,
  auto_unbox = TRUE,
  digits = 10
)

delta_panel <- function(
    data,
    x_column,
    title,
    x_label,
    reference,
    transform = "identity",
    formatter = label_number(accuracy = 0.1)
) {
  ggplot(data, aes(x = .data[[x_column]], y = config)) +
    geom_vline(
      xintercept = reference,
      linetype = "dashed",
      linewidth = 0.55,
      color = paper_colors$muted
    ) +
    geom_segment(
      aes(x = reference, xend = .data[[x_column]], yend = config),
      linewidth = 1.0,
      color = paper_colors$grid,
      lineend = "round"
    ) +
    geom_point(
      aes(fill = point_color, size = focal),
      shape = 21,
      color = paper_colors$white,
      stroke = 0.65
    ) +
    scale_fill_identity() +
    scale_size_manual(values = c("FALSE" = 3.3, "TRUE" = 4.4), guide = "none") +
    scale_x_continuous(
      trans = transform,
      labels = formatter,
      expand = expansion(mult = c(0.11, 0.13))
    ) +
    labs(title = title, x = x_label, y = NULL) +
    theme_paper(base_size = 8.8) +
    theme(
      panel.grid.major.y = element_blank(),
      axis.text.y = element_text(color = paper_colors$ink)
    )
}

p_score <- delta_panel(
  summary,
  "score_delta",
  "(A) Quality effect",
  "Mean score change vs Full",
  0,
  formatter = label_number(accuracy = 1, style_positive = "plus")
)
p_runtime <- delta_panel(
  summary,
  "runtime_ratio",
  "(B) Runtime effect",
  "Multiplier vs Full",
  1,
  transform = "log2",
  formatter = label_number(accuracy = 0.1, suffix = "x")
) +
  theme(axis.text.y = element_blank())
p_labels <- delta_panel(
  summary,
  "label_ratio",
  "(C) Search-space effect",
  "Label-count multiplier",
  1,
  transform = "log2",
  formatter = label_number(accuracy = 0.1, suffix = "x")
)
p_cap <- delta_panel(
  summary,
  "cap_hit_pct",
  "(D) Resource-limit incidence",
  "Tasks hitting timeout or label cap (%)",
  0,
  formatter = label_number(accuracy = 1, suffix = "%")
) +
  theme(axis.text.y = element_blank())

core_plot <- p_score + p_runtime + p_labels + p_cap +
  plot_layout(ncol = 2, widths = c(1.16, 1))

save_paper_plot(
  core_plot,
  file.path(figure_dir, "exp2_core_layer_delta"),
  width = 7.15,
  height = 5.35
)

pareto <- ggplot(
  summary,
  aes(x = elapsed_ms, y = stop_score, size = labels)
) +
  geom_point(
    aes(fill = point_color),
    shape = 21,
    color = paper_colors$white,
    stroke = 0.8,
    alpha = 0.95
  ) +
  geom_text_repel(
    aes(label = as.character(config)),
    color = paper_colors$ink,
    size = 2.7,
    box.padding = 0.55,
    point.padding = 0.75,
    segment.color = paper_colors$grid,
    segment.size = 0.35,
    min.segment.length = 0,
    max.overlaps = Inf,
    force = 2.5,
    force_pull = 0.35,
    max.time = 3,
    seed = 20260723
  ) +
  scale_fill_identity() +
  scale_size_continuous(
    range = c(3.5, 10),
    breaks = c(100000, 500000, 1000000),
    labels = label_number(scale_cut = cut_short_scale()),
    name = "Mean labels"
  ) +
  scale_x_log10(
    labels = label_number(scale_cut = cut_short_scale(), accuracy = 0.1),
    expand = expansion(mult = c(0.08, 0.17))
  ) +
  scale_y_continuous(
    labels = label_number(accuracy = 1),
    expand = expansion(mult = c(0.08, 0.09))
  ) +
  labs(
    title = "Ablation quality-speed landscape",
    subtitle = "Point area encodes mean explored labels",
    x = "Mean generation time (ms, log scale)",
    y = "Mean stop score",
    size = "Mean labels"
  ) +
  theme_paper() +
  theme(
    legend.position = "bottom",
    legend.direction = "horizontal",
    legend.title = element_text(
      size = 8.0,
      face = "plain",
      color = paper_colors$muted
    )
  ) +
  guides(
    size = guide_legend(
      title.position = "left",
      nrow = 1,
      byrow = TRUE
    )
  )

save_paper_plot(
  pareto,
  file.path(figure_dir, "exp2_ablation_pareto_scatter"),
  width = 7.15,
  height = 3.85
)

message("Wrote unified Exp2 figures from: ", input_path)
