#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(ggrepel)
  library(jsonlite)
  library(patchwork)
  library(scales)
  library(tidyr)
})

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1]]), winslash = "/")
} else {
  normalizePath("paper/experiments/r_visualization/plot_exp1.R", winslash = "/")
}
script_dir <- dirname(script_path)
source(file.path(script_dir, "paper_theme.R"))

repo_root <- normalizePath(file.path(script_dir, "../../.."), winslash = "/")
result_path <- file.path(
  repo_root,
  "paper/results/exp1_algorithm_comparison",
  "exp1_results_canonical_final_10alg_manuscript_20260723.json"
)
figure_dir <- file.path(repo_root, "paper/figures/exp1")

payload <- jsonlite::fromJSON(result_path, simplifyDataFrame = TRUE)
raw <- payload$results

required_columns <- c(
  "algorithm", "origin_name", "depart_time", "budget_minutes",
  "score_seed", "seed", "elapsed_ms", "stop_score_total"
)
missing_columns <- setdiff(required_columns, names(raw))
if (length(missing_columns)) {
  stop("Missing Exp1 columns: ", paste(missing_columns, collapse = ", "))
}

raw <- raw %>%
  mutate(
    algorithm_label = unname(paper_algorithm_labels[algorithm]),
    algorithm_label = if_else(
      is.na(algorithm_label),
      algorithm,
      algorithm_label
    ),
    stop_score_total = as.numeric(stop_score_total),
    elapsed_ms = as.numeric(elapsed_ms),
    budget_hours = budget_minutes / 60
  )

# First average stochastic algorithm seeds so each task has equal weight.
task <- raw %>%
  group_by(
    algorithm, algorithm_label, origin_name, depart_time,
    budget_minutes, budget_hours, score_seed
  ) %>%
  summarise(
    stop_score = mean(stop_score_total, na.rm = TRUE),
    elapsed_ms = mean(elapsed_ms, na.rm = TRUE),
    .groups = "drop"
  )

overall <- task %>%
  group_by(algorithm, algorithm_label) %>%
  summarise(
    stop_score = mean(stop_score),
    elapsed_ms = mean(elapsed_ms),
    .groups = "drop"
  ) %>%
  arrange(stop_score) %>%
  mutate(
    algorithm_label = factor(algorithm_label, levels = algorithm_label),
    method_color = paper_algorithm_color(as.character(algorithm_label)),
    emphasis = if_else(
      as.character(algorithm_label) %in% c("Ours", "NSGA-II"),
      "focal",
      "baseline"
    )
  )

score_ours <- overall$stop_score[overall$algorithm == "Ours (Full)"]
score_nsga <- overall$stop_score[overall$algorithm == "NSGA-II"]
score_gap_pct <- 100 * (score_ours - score_nsga) / score_nsga

p_score <- ggplot(overall, aes(x = stop_score, y = algorithm_label)) +
  geom_segment(
    aes(x = 0, xend = stop_score, yend = algorithm_label),
    linewidth = 1.15,
    color = paper_colors$grid,
    lineend = "round"
  ) +
  geom_point(
    aes(fill = method_color, size = emphasis),
    shape = 21,
    color = paper_colors$white,
    stroke = 0.7
  ) +
  geom_text(
    aes(
      label = scales::number(stop_score, accuracy = 0.1),
      color = method_color
    ),
    hjust = 0,
    nudge_x = max(overall$stop_score, na.rm = TRUE) * 0.045,
    size = 2.7,
    family = "serif",
    show.legend = FALSE
  ) +
  scale_fill_identity() +
  scale_color_identity() +
  scale_size_manual(values = c("baseline" = 3.4, "focal" = 4.7), guide = "none") +
  scale_x_continuous(
    labels = label_number(accuracy = 1),
    limits = c(0, max(overall$stop_score, na.rm = TRUE) * 1.32),
    expand = expansion(mult = c(0, 0))
  ) +
  labs(
    title = "Mean stop score across matched tasks",
    x = "Mean stop score (higher is better)",
    y = NULL
  ) +
  theme_paper() +
  theme(
    panel.grid.major.y = element_blank(),
    axis.text.y = element_text(
      color = paper_colors$ink,
      margin = margin(r = 4)
    )
  )

label_offsets <- tibble::tribble(
  ~algorithm_label, ~nudge_x, ~nudge_y,
  "Ours", 0.05, 22,
  "NSGA-II", 0.05, -18,
  "ILS+2opt", 0.05, 17,
  "ALNS", 0.05, 20,
  "VNS", 0.05, -15,
  "SA", 0.05, -20,
  "McRAPTOR", 0.05, 18,
  "Greedy", 0.05, -17,
  "DynPref", 0.05, 17,
  "Pure RAPTOR", 0.05, -20
)

scatter_data <- overall %>%
  mutate(algorithm_label = as.character(algorithm_label)) %>%
  left_join(label_offsets, by = "algorithm_label")

p_tradeoff <- ggplot(
  scatter_data,
  aes(x = elapsed_ms, y = stop_score)
) +
  geom_point(
    aes(fill = method_color, size = emphasis),
    shape = 21,
    color = paper_colors$white,
    stroke = 0.8
  ) +
  ggrepel::geom_text_repel(
    aes(label = algorithm_label),
    color = paper_colors$ink,
    size = 2.65,
    family = "serif",
    box.padding = 0.25,
    point.padding = 0.2,
    min.segment.length = 0,
    segment.color = paper_colors$grid,
    segment.size = 0.35,
    max.overlaps = Inf,
    seed = 20260723
  ) +
  scale_fill_identity() +
  scale_size_manual(values = c("baseline" = 3.6, "focal" = 5.0), guide = "none") +
  scale_x_log10(
    labels = scales::label_number(
      scale_cut = scales::cut_short_scale(),
      accuracy = 0.1
    )
  ) +
  scale_y_continuous(
    labels = label_number(accuracy = 1),
    expand = expansion(mult = c(0.07, 0.12))
  ) +
  labs(
    title = "Score-runtime trade-off",
    x = "Mean generation time (ms, log scale)",
    y = "Mean stop score"
  ) +
  theme_paper()

overview <- p_score + p_tradeoff +
  plot_layout(widths = c(1.0, 1.15)) +
  plot_annotation(tag_levels = "A") &
  paper_tag_theme

save_paper_plot(
  overview,
  file.path(
    figure_dir,
    "exp1_score_guided_multiseed_overview_2h4h6h8h"
  ),
  width = 7.15,
  height = 3.55
)

budget_summary <- task %>%
  group_by(algorithm_label, budget_hours) %>%
  summarise(
    stop_score = mean(stop_score),
    .groups = "drop"
  ) %>%
  mutate(
    algorithm_label = as.character(algorithm_label),
    method_color = paper_algorithm_color(algorithm_label),
    emphasis = case_when(
      algorithm_label == "Ours" ~ "ours",
      algorithm_label == "NSGA-II" ~ "reference",
      TRUE ~ "baseline"
    )
  )

end_labels <- budget_summary %>%
  filter(budget_hours == max(budget_hours)) %>%
  mutate(
    label = if_else(
      algorithm_label %in% c("Ours", "NSGA-II"),
      algorithm_label,
      ""
    )
  )

p_budget <- ggplot(
  budget_summary,
  aes(
    x = budget_hours,
    y = stop_score,
    group = algorithm_label,
    color = method_color
  )
) +
  geom_line(
    aes(linewidth = emphasis, alpha = emphasis),
    lineend = "round"
  ) +
  geom_point(
    aes(size = emphasis, alpha = emphasis),
    shape = 16
  ) +
  geom_text_repel(
    data = end_labels %>% filter(label != ""),
    aes(label = label),
    direction = "y",
    nudge_x = 0.35,
    hjust = 0,
    size = 2.7,
    family = "serif",
    segment.color = paper_colors$grid,
    segment.size = 0.35,
    seed = 20260723,
    show.legend = FALSE
  ) +
  scale_color_identity() +
  scale_linewidth_manual(
    values = c("baseline" = 0.65, "reference" = 1.2, "ours" = 1.45),
    guide = "none"
  ) +
  scale_size_manual(
    values = c("baseline" = 1.55, "reference" = 2.45, "ours" = 2.8),
    guide = "none"
  ) +
  scale_alpha_manual(
    values = c("baseline" = 0.52, "reference" = 1, "ours" = 1),
    guide = "none"
  ) +
  scale_x_continuous(
    breaks = c(2, 4, 6, 8),
    labels = paste0(c(2, 4, 6, 8), "h"),
    limits = c(1.8, 8.9)
  ) +
  scale_y_continuous(
    labels = label_number(accuracy = 1),
    expand = expansion(mult = c(0.03, 0.10))
  ) +
  labs(
    title = "Budget-wise mean stop score",
    x = "Time budget",
    y = "Mean stop score"
  ) +
  theme_paper() +
  theme(panel.grid.major.x = element_line(color = paper_colors$grid, linewidth = 0.35))

paired <- task %>%
  filter(algorithm %in% c("Ours (Full)", "NSGA-II")) %>%
  select(
    algorithm, origin_name, depart_time, budget_minutes,
    budget_hours, score_seed, stop_score
  ) %>%
  pivot_wider(names_from = algorithm, values_from = stop_score) %>%
  mutate(gap = `Ours (Full)` - `NSGA-II`)

gap_means <- paired %>%
  group_by(budget_hours) %>%
  summarise(mean_gap = mean(gap), .groups = "drop")

gap_range <- range(paired$gap, na.rm = TRUE)
gap_span <- diff(gap_range)
gap_label_y <- gap_range[2] + 0.12 * gap_span
gap_upper <- gap_range[2] + 0.22 * gap_span
gap_lower <- gap_range[1] - 0.04 * gap_span
gap_means <- gap_means %>%
  mutate(
    label_y = gap_label_y,
    label = sprintf("%+.1f", mean_gap)
  )

p_gap <- ggplot(
  paired,
  aes(x = factor(budget_hours), y = gap)
) +
  geom_violin(
    fill = scales::alpha(paper_colors$ours, 0.13),
    color = scales::alpha(paper_colors$ours, 0.55),
    linewidth = 0.55,
    width = 0.82,
    trim = TRUE
  ) +
  geom_boxplot(
    width = 0.20,
    outlier.shape = NA,
    fill = paper_colors$white,
    color = paper_colors$ink,
    linewidth = 0.45
  ) +
  geom_hline(
    yintercept = 0,
    linetype = "dashed",
    linewidth = 0.55,
    color = paper_colors$muted
  ) +
  geom_point(
    data = gap_means,
    aes(x = factor(budget_hours), y = mean_gap),
    shape = 23,
    size = 3,
    stroke = 0.55,
    fill = paper_colors$ours,
    color = paper_colors$white
  ) +
  geom_text(
    data = gap_means,
    aes(
      x = factor(budget_hours),
      y = label_y,
      label = label
    ),
    size = 2.4,
    family = "serif",
    color = paper_colors$ours,
    lineheight = 0.92
  ) +
  scale_x_discrete(labels = function(x) paste0(x, "h")) +
  scale_y_continuous(
    labels = label_number(accuracy = 1),
    limits = c(gap_lower, gap_upper),
    expand = expansion(mult = c(0, 0))
  ) +
  labs(
    title = "Paired differences (Ours - NSGA-II)",
    x = "Time budget",
    y = "Stop-score difference"
  ) +
  theme_paper() +
  theme(panel.grid.major.x = element_blank())

budget_plot <- p_budget + p_gap +
  plot_layout(widths = c(1.15, 1.0)) +
  plot_annotation(tag_levels = "A") &
  paper_tag_theme

save_paper_plot(
  budget_plot,
  file.path(
    figure_dir,
    "exp1_score_guided_multiseed_budget_2h4h6h8h"
  ),
  width = 7.15,
  height = 3.55
)

heatmap_path <- file.path(
  repo_root,
  "paper/results/exp1_algorithm_comparison",
  "underperformance_origin_budget_20260723.csv"
)
if (file.exists(heatmap_path)) {
  heatmap_data <- read.csv(heatmap_path, check.names = FALSE) %>%
    mutate(
      budget_hours = budget_minutes / 60,
      origin_label = tools::toTitleCase(gsub("-", " ", origin_name)),
      origin_label = factor(
        origin_label,
        levels = rev(unique(origin_label))
      )
    )

  p_heatmap <- ggplot(
    heatmap_data,
    aes(x = factor(budget_hours), y = origin_label, fill = mean_gap)
  ) +
    geom_tile(color = paper_colors$white, linewidth = 0.8) +
    geom_text(
      aes(label = sprintf("%+.0f", mean_gap)),
      size = 2.65,
      family = "serif",
      color = paper_colors$ink
    ) +
    scale_fill_gradient2(
      low = "#F3B6B1",
      mid = paper_colors$white,
      high = "#AFC8FA",
      midpoint = 0,
      name = "Mean gap"
    ) +
    scale_x_discrete(labels = function(x) paste0(x, "h")) +
    labs(
      title = "Mean paired score difference by origin and budget",
      x = "Time budget",
      y = NULL
    ) +
    theme_paper() +
    theme(
      panel.grid = element_blank(),
      legend.position = "right",
      axis.text.y = element_text(color = paper_colors$ink)
    )

  save_paper_plot(
    p_heatmap,
    file.path(figure_dir, "underperformance_heatmap_20260723"),
    width = 5.2,
    height = 3.9
  )
}

message("Wrote unified Exp1 figures to: ", figure_dir)
