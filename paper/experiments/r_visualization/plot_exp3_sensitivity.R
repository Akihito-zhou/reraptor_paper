#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(ggrepel)
  library(patchwork)
  library(scales)
})

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1]]), winslash = "/")
} else {
  normalizePath(
    "paper/experiments/r_visualization/plot_exp3_sensitivity.R",
    winslash = "/"
  )
}
script_dir <- dirname(script_path)
source(file.path(script_dir, "paper_theme.R"))
repo_root <- normalizePath(file.path(script_dir, "../../.."), winslash = "/")

result_dir <- file.path(repo_root, "paper/results/exp3_parameter_sensitivity")
figure_dir <- file.path(repo_root, "paper/figures/exp3")
overall <- utils::read.csv(
  file.path(result_dir, "sensitivity_canonical_summary_20260727.csv"),
  check.names = FALSE
)
paired <- utils::read.csv(
  file.path(
    result_dir,
    "sensitivity_canonical_paired_vs_default_20260727.csv"
  ),
  check.names = FALSE
)
interaction <- utils::read.csv(
  file.path(result_dir, "sensitivity_canonical_interaction_20260727.csv"),
  check.names = FALSE
)

if (
  nrow(overall) != 18 ||
  nrow(paired) != 18 ||
  nrow(interaction) != 9 ||
  any(overall$task_count != 600) ||
  any(paired$paired_tasks != 600) ||
  any(interaction$task_count != 72)
) {
  stop("Sensitivity summaries do not match the frozen panel dimensions.")
}

joined <- overall %>%
  inner_join(
    paired %>%
      select(
        config_id,
        mean_score_delta_vs_default,
        bootstrap_ci95_low,
        bootstrap_ci95_high
      ),
    by = "config_id"
  )

beam <- joined %>%
  filter(config_id %in% c("w10", "w25", "default", "w100", "w200")) %>%
  mutate(
    beam_width = factor(
      beam_width,
      levels = c(10, 25, 50, 100, 200)
    ),
    cap_label = paste0(number(100 * resource_cap_rate, accuracy = 0.1), "%"),
    default_setting = config_id == "default"
  )

p_beam <- ggplot(
  beam,
  aes(
    x = beam_width,
    y = mean_score_delta_vs_default,
    group = 1
  )
) +
  geom_hline(
    yintercept = 0,
    linetype = "dashed",
    linewidth = 0.45,
    color = paper_colors$muted
  ) +
  geom_line(linewidth = 0.65, color = paper_colors$baseline_dark) +
  geom_errorbar(
    aes(
      ymin = bootstrap_ci95_low,
      ymax = bootstrap_ci95_high
    ),
    width = 0.13,
    linewidth = 0.55,
    color = paper_colors$baseline_dark
  ) +
  geom_point(
    aes(fill = default_setting),
    shape = 21,
    size = 3.1,
    stroke = 0.65,
    color = paper_colors$ink
  ) +
  geom_text(
    data = beam %>% filter(config_id != "w10"),
    aes(label = paste0("Cap ", cap_label)),
    vjust = -1.1,
    size = 2.5,
    color = paper_colors$muted,
    family = "serif"
  ) +
  geom_text(
    data = beam %>% filter(config_id == "w10"),
    aes(label = paste0("Cap ", cap_label)),
    hjust = 0,
    vjust = 1.35,
    nudge_x = 0.25,
    size = 2.5,
    color = paper_colors$muted,
    family = "serif"
  ) +
  scale_fill_manual(
    values = c("FALSE" = paper_colors$white, "TRUE" = paper_colors$ours),
    guide = "none"
  ) +
  scale_x_discrete(
    expand = expansion(add = c(0.85, 0.45))
  ) +
  scale_y_continuous(
    labels = label_number(accuracy = 0.1, style_positive = "plus"),
    expand = expansion(mult = c(0.18, 0.32))
  ) +
  labs(
    title = "(A) Bucket beam width",
    x = "Beam width W",
    y = "Paired score change vs default"
  ) +
  theme_paper(base_size = 8.9) +
  theme(panel.grid.major.x = element_blank())

cap_tradeoff <- joined %>%
  filter(
    config_id %in% c(
      "cap15_10",
      "default",
      "cap60_40",
      "cap_uncapped"
    )
  ) %>%
  mutate(
    setting = recode(
      config_id,
      "cap15_10" = "15/10",
      "default" = "30/20 (default)",
      "cap60_40" = "60/40",
      "cap_uncapped" = "Uncapped"
    ),
    cap_pct = 100 * resource_cap_rate,
    label_x = case_when(
      config_id == "cap15_10" ~ 5.0,
      config_id == "default" ~ 10.0,
      config_id == "cap60_40" ~ 45.0,
      TRUE ~ 62.0
    ),
    label_y = case_when(
      config_id == "cap15_10" ~ 670,
      config_id == "default" ~ 930,
      config_id == "cap60_40" ~ 1022,
      TRUE ~ 700
    ),
    label_hjust = case_when(
      config_id %in% c("cap60_40", "cap_uncapped") ~ 1,
      TRUE ~ 0
    ),
    default_setting = config_id == "default"
  )

p_cap <- ggplot(
  cap_tradeoff,
  aes(x = cap_pct, y = mean_stop_score)
) +
  geom_path(
    aes(group = 1),
    linewidth = 0.6,
    color = paper_colors$grid
  ) +
  geom_point(
    aes(fill = default_setting, size = mean_labels),
    shape = 21,
    stroke = 0.7,
    color = paper_colors$ink
  ) +
  geom_text(
    data = cap_tradeoff,
    aes(
      x = label_x,
      y = label_y,
      label = setting,
      hjust = label_hjust
    ),
    inherit.aes = FALSE,
    family = "serif",
    size = 2.6,
    color = paper_colors$ink
  ) +
  scale_fill_manual(
    values = c("FALSE" = paper_colors$white, "TRUE" = paper_colors$ours),
    guide = "none"
  ) +
  scale_size_area(
    max_size = 5.4,
    labels = label_number(scale = 1e-3, accuracy = 1, suffix = "k"),
    breaks = c(5000, 100000, 500000),
    name = "Mean labels"
  ) +
  scale_x_continuous(
    labels = label_percent(scale = 1, accuracy = 1),
    limits = c(-4, 74),
    breaks = c(0, 20, 40, 60)
  ) +
  scale_y_continuous(
    labels = label_number(accuracy = 50),
    limits = c(620, 1045),
    breaks = c(700, 800, 900, 1000)
  ) +
  labs(
    title = "(B) Candidate-cap trade-off",
    x = "Tasks hitting a resource limit",
    y = "Mean Stop Score"
  ) +
  theme_paper(base_size = 8.9) +
  theme(
    legend.position = c(0.97, 0.04),
    legend.justification = c(1, 0),
    legend.direction = "horizontal",
    legend.key.width = unit(0.8, "lines")
  )

coefficient_labels <- c(
  "reward5000" = "Reward weight: 0.5x",
  "reward20000" = "Reward weight: 2x",
  "sph0" = "SPH weight: 0",
  "sph2p5" = "SPH weight: 0.5x",
  "sph10" = "SPH weight: 2x",
  "time0" = "Time weight: 0",
  "time0p05" = "Time weight: 0.5x",
  "time0p2" = "Time weight: 2x",
  "neg0p5" = "Negative penalty: 0.5x",
  "neg2" = "Negative penalty: 2x"
)
coefficients <- joined %>%
  filter(config_id %in% names(coefficient_labels)) %>%
  mutate(
    setting = unname(coefficient_labels[config_id]),
    setting = factor(setting, levels = rev(unname(coefficient_labels)))
  )

p_coeff <- ggplot(
  coefficients,
  aes(x = mean_score_delta_vs_default, y = setting)
) +
  geom_vline(
    xintercept = 0,
    linetype = "dashed",
    linewidth = 0.45,
    color = paper_colors$muted
  ) +
  geom_errorbar(
    aes(xmin = bootstrap_ci95_low, xmax = bootstrap_ci95_high),
    orientation = "y",
    width = 0.24,
    linewidth = 0.5,
    color = paper_colors$baseline_dark
  ) +
  geom_point(
    shape = 21,
    size = 2.7,
    fill = paper_colors$white,
    color = paper_colors$ink,
    stroke = 0.65
  ) +
  scale_x_continuous(
    labels = label_number(accuracy = 0.05, style_positive = "plus"),
    breaks = c(-0.10, -0.05, 0, 0.05, 0.10),
    limits = c(-0.13, 0.13)
  ) +
  labs(
    title = "(C) Surrogate coefficients",
    x = "Paired score change vs default (95% CI)",
    y = NULL
  ) +
  theme_paper(base_size = 8.9) +
  theme(
    panel.grid.major.y = element_blank(),
    axis.text.y = element_text(color = paper_colors$ink)
  )

interaction_plot <- interaction %>%
  mutate(
    beam_width = factor(beam_width, levels = c(25, 50, 100)),
    candidate_cap = factor(
      candidate_cap,
      levels = c("60/40", "30/20", "15/10")
    ),
    delta_label = if_else(
      abs(mean_score_delta_vs_default_subset) < 0.005,
      "0",
      number(
        mean_score_delta_vs_default_subset,
        accuracy = 1,
        style_positive = "plus"
      )
    ),
    cell_label = paste0(
      delta_label,
      "\n",
      number(100 * resource_cap_rate, accuracy = 1),
      "% cap"
    ),
    text_color = if_else(
      abs(mean_score_delta_vs_default_subset) > 125,
      paper_colors$white,
      paper_colors$ink
    )
  )

p_interaction <- ggplot(
  interaction_plot,
  aes(
    x = beam_width,
    y = candidate_cap,
    fill = mean_score_delta_vs_default_subset
  )
) +
  geom_tile(color = paper_colors$white, linewidth = 0.75) +
  geom_text(
    aes(label = cell_label, color = text_color),
    family = "serif",
    size = 2.65,
    lineheight = 0.9
  ) +
  scale_color_identity() +
  scale_fill_gradient2(
    low = paper_colors$negative,
    mid = paper_colors$white,
    high = paper_colors$ours,
    midpoint = 0,
    limits = c(-210, 210),
    oob = squish,
    name = expression(Delta * " score")
  ) +
  labs(
    title = "(D) Width × candidate-cap interaction",
    x = "Beam width W",
    y = "Candidate cap (short/long budget)"
  ) +
  theme_paper(base_size = 8.9) +
  theme(
    panel.grid = element_blank(),
    legend.position = "right",
    legend.key.height = unit(1.2, "lines")
  )

combined <- (p_beam + p_cap) / (p_coeff + p_interaction) +
  plot_layout(heights = c(0.91, 1.16))

save_paper_plot(
  combined,
  file.path(figure_dir, "exp3_hyperparameter_sensitivity"),
  width = 7.15,
  height = 5.65,
  dpi = 360
)

message(
  "Saved vector PDF and high-resolution PNG: ",
  file.path(figure_dir, "exp3_hyperparameter_sensitivity")
)
