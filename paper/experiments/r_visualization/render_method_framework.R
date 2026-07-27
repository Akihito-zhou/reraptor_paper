#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(grid)
})

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1]]), winslash = "/")
} else {
  normalizePath(
    "paper/experiments/r_visualization/render_method_framework.R",
    winslash = "/"
  )
}
script_dir <- dirname(script_path)
source(file.path(script_dir, "paper_theme.R"))
repo_root <- normalizePath(file.path(script_dir, "../../.."), winslash = "/")
output_base <- file.path(
  repo_root,
  "paper/figures/method/ours_framework_flow"
)

fig <- list(
  ink = paper_colors$ink,
  muted = paper_colors$muted,
  faint = paper_colors$faint,
  rule = "#AFAFAF",
  grid = paper_colors$grid,
  panel = "#F7F7F7",
  blue_pale = "#EAF3F8",
  white = paper_colors$white,
  blue = paper_colors$ours,
  orange = paper_colors$reference,
  green = paper_colors$accent
)

txt <- function(
    text, x, y,
    fontsize = 9,
    col = fig$ink,
    fontface = "plain",
    just = c("centre", "centre"),
    lineheight = 1.05
) {
  grid.text(
    text,
    x = unit(x, "npc"),
    y = unit(y, "npc"),
    just = just,
    gp = gpar(
      fontsize = fontsize,
      col = col,
      fontface = fontface,
      fontfamily = "serif",
      lineheight = lineheight
    )
  )
}

box <- function(
    x, y, width, height,
    fill = fig$white,
    col = fig$rule,
    lwd = 0.75,
    lty = 1
) {
  grid.rect(
    x = unit(x, "npc"),
    y = unit(y, "npc"),
    width = unit(width, "npc"),
    height = unit(height, "npc"),
    gp = gpar(fill = fill, col = col, lwd = lwd, lty = lty)
  )
}

polyline_arrow <- function(
    x, y,
    col = fig$ink,
    lwd = 0.8,
    lty = 1,
    arrow_end = TRUE
) {
  grid.lines(
    x = unit(x, "npc"),
    y = unit(y, "npc"),
    arrow = if (arrow_end) {
      arrow(
        angle = 23,
        length = unit(0.060, "inches"),
        ends = "last",
        type = "closed"
      )
    } else {
      NULL
    },
    gp = gpar(col = col, lwd = lwd, lty = lty, lineend = "butt")
  )
}

section_label <- function(letter, title, x) {
  txt(
    paste0("(", letter, ")  ", title),
    x,
    0.920,
    fontsize = 10.2,
    fontface = "bold",
    just = c("left", "centre")
  )
}

input_box <- function(y, title, body) {
  box(0.120, y, 0.185, 0.170, fill = fig$panel)
  txt(
    title,
    0.040,
    y + 0.035,
    fontsize = 9.2,
    fontface = "bold",
    just = c("left", "centre")
  )
  txt(
    body,
    0.040,
    y - 0.025,
    fontsize = 8.3,
    col = fig$muted,
    just = c("left", "centre"),
    lineheight = 1.08
  )
}

stage_box <- function(x, title, body, width = 0.095) {
  box(x, 0.605, width, 0.170, fill = fig$white, col = fig$muted)
  txt(title, x, 0.640, fontsize = 9.2, fontface = "bold")
  txt(
    body,
    x,
    0.570,
    fontsize = 8.3,
    col = fig$muted,
    lineheight = 1.08
  )
}

support_box <- function(x, width, title, body, accent = fig$blue) {
  box(x, 0.310, width, 0.160, fill = fig$panel, col = fig$rule, lwd = 0.65)
  grid.lines(
    x = unit(c(x - width / 2, x + width / 2), "npc"),
    y = unit(c(0.390, 0.390), "npc"),
    gp = gpar(col = accent, lwd = 1.4)
  )
  txt(title, x, 0.350, fontsize = 8.8, fontface = "bold")
  txt(body, x, 0.280, fontsize = 7.8, col = fig$muted, lineheight = 1.05)
}

decision <- function(x, y, width, height, label) {
  grid.polygon(
    x = unit(c(x, x + width / 2, x, x - width / 2), "npc"),
    y = unit(c(y + height / 2, y, y - height / 2, y), "npc"),
    gp = gpar(fill = fig$white, col = fig$muted, lwd = 0.75)
  )
  txt(label, x, y, fontsize = 8.0, lineheight = 1.0)
}

route_schematic <- function() {
  route_x <- c(0.857, 0.884, 0.910, 0.938, 0.963)
  route_y <- c(0.545, 0.585, 0.565, 0.610, 0.585)
  grid.lines(
    x = unit(route_x, "npc"),
    y = unit(route_y, "npc"),
    gp = gpar(
      col = fig$blue,
      lwd = 1.8,
      lineend = "round",
      linejoin = "round"
    )
  )
  for (i in seq_along(route_x)) {
    grid.circle(
      x = unit(route_x[i], "npc"),
      y = unit(route_y[i], "npc"),
      r = unit(ifelse(i %in% c(1, length(route_x)), 0.0065, 0.0042), "npc"),
      gp = gpar(
        fill = ifelse(i == 1, fig$green, ifelse(
          i == length(route_x), fig$orange, fig$white
        )),
        col = ifelse(i %in% c(1, length(route_x)), fig$ink, fig$blue),
        lwd = 0.6
      )
    )
  }
}

draw_framework <- function() {
  grid.newpage()
  grid.rect(gp = gpar(fill = fig$white, col = NA))

  section_label("A", "Problem instance", 0.025)
  section_label("B", "ReRAPTOR search", 0.255)
  section_label("C", "Result", 0.845)
  for (x in c(0.235, 0.830)) {
    grid.lines(
      x = unit(c(x, x), "npc"),
      y = unit(c(0.105, 0.875), "npc"),
      gp = gpar(col = fig$grid, lwd = 0.65)
    )
  }

  # The two inputs a reader needs to understand the planning problem.
  input_box(
    0.655,
    "Travel request",
    "origin, departure time,\nand time budget"
  )
  input_box(
    0.405,
    "Transit network",
    "scheduled services,\nstops, and connections"
  )

  # Both inputs feed the same search initialization.
  for (y in c(0.655, 0.405)) {
    polyline_arrow(
      c(0.2125, 0.228),
      c(y, y),
      col = fig$faint,
      lwd = 0.65,
      arrow_end = FALSE
    )
  }
  polyline_arrow(
    c(0.228, 0.228),
    c(0.405, 0.655),
    col = fig$faint,
    lwd = 0.65,
    arrow_end = FALSE
  )

  # One clear left-to-right story: generate, update, filter, and test.
  stage_x <- c(0.300, 0.415, 0.535, 0.660)
  stage_box(stage_x[1], "Initialize", "origin\nlabel")
  stage_box(stage_x[2], "Expand", "scheduled\nservices")
  stage_box(stage_x[3], "Update", "candidate\nroute")
  stage_box(stage_x[4], "Prune", "rank and\nretain", width = 0.108)
  # Keep the decision label comfortably inside the diamond at print size.
  # Shifting the centre left preserves the existing right-hand output boundary.
  decision(0.775, 0.605, 0.094, 0.185, "Finished?")

  polyline_arrow(c(0.228, 0.252), c(0.605, 0.605))
  polyline_arrow(c(0.348, 0.368), c(0.605, 0.605))
  polyline_arrow(c(0.463, 0.488), c(0.605, 0.605))
  polyline_arrow(c(0.583, 0.606), c(0.605, 0.605))
  polyline_arrow(c(0.714, 0.728), c(0.605, 0.605))

  # Continue expanding until no further useful candidate remains.
  polyline_arrow(
    c(0.775, 0.775, 0.415, 0.415),
    c(0.698, 0.795, 0.795, 0.690),
    col = fig$muted,
    lwd = 0.7
  )
  txt("No: continue search", 0.600, 0.820, fontsize = 7.6, col = fig$muted)

  # Supporting mechanisms are kept below the main flow, with no equations.
  support_box(
    0.440,
    0.210,
    "Task-specific scoring",
    "reward and\nacceptance criteria",
    fig$blue
  )
  support_box(
    0.665,
    0.215,
    "Search controls",
    "beam  |  dominance\nrepeat/short-hop penalty",
    fig$orange
  )
  polyline_arrow(
    c(0.440, 0.440, 0.520),
    c(0.390, 0.475, 0.475),
    col = fig$blue,
    lwd = 0.65,
    lty = 2,
    arrow_end = FALSE
  )
  polyline_arrow(
    c(0.665, 0.665),
    c(0.390, 0.520),
    col = fig$orange,
    lwd = 0.65,
    lty = 2,
    arrow_end = FALSE
  )

  # Accepted output: a route, not another formula panel.
  polyline_arrow(c(0.822, 0.845), c(0.605, 0.605), col = fig$blue, lwd = 1.0)
  # Keep the branch label clear of both the arrow and the section divider.
  txt("Yes", 0.854, 0.655, fontsize = 7.5, col = fig$blue)
  txt("Selected itinerary", 0.915, 0.720, fontsize = 9.2, fontface = "bold")
  route_schematic()
  txt("origin", 0.857, 0.505, fontsize = 7.0, col = fig$muted)
  txt("destination", 0.963, 0.535, fontsize = 7.0, col = fig$muted)
  txt(
    "route  |  score  |  travel time",
    0.915,
    0.385,
    fontsize = 7.5,
    col = fig$muted
  )
}

dir.create(dirname(output_base), recursive = TRUE, showWarnings = FALSE)

framework_cairo_source <- paste0(output_base, ".cairo-source.pdf")
grDevices::cairo_pdf(
  filename = framework_cairo_source,
  width = 7.15,
  height = 3.0,
  bg = fig$white
)
draw_framework()
dev.off()
convert_to_pdf15(framework_cairo_source, paste0(output_base, ".pdf"))

if (requireNamespace("ragg", quietly = TRUE)) {
  ragg::agg_png(
    filename = paste0(output_base, ".png"),
    width = 2288,
    height = 960,
    units = "px",
    res = 320,
    background = fig$white
  )
} else {
  png(
    filename = paste0(output_base, ".png"),
    width = 2288,
    height = 960,
    res = 320,
    type = "cairo",
    bg = fig$white
  )
}
draw_framework()
dev.off()

message("Wrote method framework to: ", dirname(output_base))
