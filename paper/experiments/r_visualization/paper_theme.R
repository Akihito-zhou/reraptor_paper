#!/usr/bin/env Rscript

# Shared visual language for all manuscript figures.
# The palette and typography follow a restrained journal-figure style:
# serif text, thin neutral structure, and color only for data encoding.

paper_colors <- list(
  ink = "#1A1A1A",
  muted = "#4D4D4D",
  faint = "#777777",
  grid = "#D9D9D9",
  panel = "#F3F3F3",
  white = "#FFFFFF",
  ours = "#0072B2",
  reference = "#D55E00",
  accent = "#009E73",
  negative = "#B2182B",
  baseline = "#A6A6A6",
  baseline_dark = "#595959"
)

paper_algorithm_labels <- c(
  "Ours (Full)" = "Ours",
  "NSGA-II" = "NSGA-II",
  "ILS+2opt" = "ILS+2opt",
  "ZhouWang2025-ALNS (adapted)" = "ALNS",
  "VNS" = "VNS",
  "SA" = "SA",
  "McRAPTOR" = "McRAPTOR",
  "Greedy (L=3)" = "Greedy",
  "Zhang2025-DynPref (adapted)" = "DynPref",
  "Pure RAPTOR" = "Pure RAPTOR"
)

paper_algorithm_color <- function(label) {
  ifelse(
    label == "Ours",
    paper_colors$ours,
    ifelse(
      label == "NSGA-II",
      paper_colors$reference,
      paper_colors$baseline
    )
  )
}

theme_paper <- function(base_size = 9.0, base_family = "serif") {
  ggplot2::theme_minimal(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      text = ggplot2::element_text(color = paper_colors$ink),
      plot.title = ggplot2::element_text(
        size = base_size * 1.05,
        face = "bold",
        hjust = 0,
        margin = ggplot2::margin(b = 3)
      ),
      plot.subtitle = ggplot2::element_text(
        size = base_size * 0.88,
        color = paper_colors$muted,
        margin = ggplot2::margin(b = 5)
      ),
      plot.caption = ggplot2::element_text(
        size = base_size * 0.78,
        color = paper_colors$muted,
        hjust = 0,
        margin = ggplot2::margin(t = 4)
      ),
      axis.title = ggplot2::element_text(
        size = base_size * 0.92,
        face = "plain"
      ),
      axis.text = ggplot2::element_text(
        size = base_size * 0.84,
        color = paper_colors$muted
      ),
      panel.grid.major = ggplot2::element_line(
        color = paper_colors$grid,
        linewidth = 0.28
      ),
      panel.grid.minor = ggplot2::element_blank(),
      panel.grid.major.y = ggplot2::element_line(
        color = paper_colors$grid,
        linewidth = 0.35
      ),
      panel.grid.major.x = ggplot2::element_blank(),
      panel.background = ggplot2::element_rect(
        fill = paper_colors$white,
        color = NA
      ),
      plot.background = ggplot2::element_rect(
        fill = paper_colors$white,
        color = NA
      ),
      legend.position = "top",
      legend.justification = "left",
      legend.title = ggplot2::element_blank(),
      legend.text = ggplot2::element_text(
        size = base_size * 0.82,
        color = paper_colors$muted
      ),
      legend.key = ggplot2::element_blank(),
      strip.background = ggplot2::element_rect(
        fill = paper_colors$white,
        color = NA
      ),
      strip.text = ggplot2::element_text(
        size = base_size * 0.88,
        face = "bold",
        color = paper_colors$ink
      ),
      plot.margin = ggplot2::margin(5, 7, 5, 5)
    )
}

paper_tag_theme <- ggplot2::theme(
  plot.tag = ggplot2::element_text(
    face = "bold",
    color = paper_colors$ink,
    family = "serif",
    size = 9.5
  ),
  plot.tag.position = c(0.02, 0.985)
)

convert_to_pdf15 <- function(source_path, target_path) {
  converter <- Sys.which("pdftocairo")
  if (!nzchar(converter)) {
    stop("pdftocairo is required to create embedded-font PDF 1.5 figures.")
  }

  status <- system2(
    converter,
    args = c(
      "-pdf",
      shQuote(normalizePath(source_path, winslash = "/", mustWork = TRUE)),
      shQuote(normalizePath(
        dirname(target_path),
        winslash = "/",
        mustWork = TRUE
      ) |> file.path(basename(target_path)))
    )
  )
  if (!identical(status, 0L) || !file.exists(target_path)) {
    stop("PDF 1.5 conversion failed for: ", source_path)
  }
  unlink(source_path)
}

save_paper_plot <- function(
    plot,
    output_base,
    width,
    height,
    dpi = 320,
    bg = paper_colors$white
) {
  dir.create(dirname(output_base), recursive = TRUE, showWarnings = FALSE)
  pdf_path <- paste0(output_base, ".pdf")
  cairo_source <- paste0(output_base, ".cairo-source.pdf")

  ggplot2::ggsave(
    cairo_source,
    plot = plot,
    device = grDevices::cairo_pdf,
    width = width,
    height = height,
    units = "in",
    bg = bg
  )
  convert_to_pdf15(cairo_source, pdf_path)

  if (requireNamespace("ragg", quietly = TRUE)) {
    ggplot2::ggsave(
      paste0(output_base, ".png"),
      plot = plot,
      device = ragg::agg_png,
      width = width,
      height = height,
      units = "in",
      dpi = dpi,
      bg = bg
    )
  } else {
    ggplot2::ggsave(
      paste0(output_base, ".png"),
      plot = plot,
      device = "png",
      type = "cairo",
      width = width,
      height = height,
      units = "in",
      dpi = dpi,
      bg = bg
    )
  }
}

format_runtime <- function(x) {
  dplyr::case_when(
    x >= 1000 ~ paste0(scales::number(x / 1000, accuracy = 0.1), " s"),
    TRUE ~ paste0(scales::number(x, accuracy = 1), " ms")
  )
}
