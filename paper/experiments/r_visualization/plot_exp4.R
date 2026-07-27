#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(jsonlite)
  library(patchwork)
  library(scales)
  library(tibble)
})

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1]]), winslash = "/")
} else {
  normalizePath("paper/experiments/r_visualization/plot_exp4.R", winslash = "/")
}
script_dir <- dirname(script_path)
source(file.path(script_dir, "paper_theme.R"))

repo_root <- normalizePath(file.path(script_dir, "../../.."), winslash = "/")
case_path <- file.path(
  repo_root,
  "paper/results/exp4_route_visualization/exp4_cases.json"
)
route_dir <- file.path(
  repo_root,
  "paper/results/exp4_route_visualization/routes"
)
geojson_path <- file.path(
  repo_root,
  "apps/api/data/base/fukuoka_city.geojson"
)
figure_dir <- file.path(repo_root, "paper/figures/exp4")

read_json_list <- function(path) {
  if (!file.exists(path)) {
    stop("Required JSON file not found: ", path)
  }
  jsonlite::fromJSON(path, simplifyVector = FALSE)
}

ring_to_frame <- function(ring, feature_id, polygon_id, ring_id) {
  if (!length(ring)) {
    return(tibble())
  }
  coords <- do.call(rbind, lapply(ring, function(point) {
    as.numeric(unlist(point))
  }))
  if (is.null(dim(coords)) || ncol(coords) < 2) {
    return(tibble())
  }
  tibble(
    lon = coords[, 1],
    lat = coords[, 2],
    group = paste(feature_id, polygon_id, ring_id, sep = "-")
  )
}

flatten_geojson <- function(path) {
  if (!file.exists(path)) {
    warning(
      "Optional city-boundary GeoJSON not found; ",
      "rendering route-only panels."
    )
    return(tibble(
      lon = double(),
      lat = double(),
      group = character()
    ))
  }
  geo <- read_json_list(path)
  rows <- list()
  row_index <- 1

  for (feature_id in seq_along(geo$features)) {
    geometry <- geo$features[[feature_id]]$geometry
    if (is.null(geometry) || is.null(geometry$coordinates)) {
      next
    }

    if (identical(geometry$type, "Polygon")) {
      polygons <- list(geometry$coordinates)
    } else if (identical(geometry$type, "MultiPolygon")) {
      polygons <- geometry$coordinates
    } else {
      next
    }

    for (polygon_id in seq_along(polygons)) {
      rings <- polygons[[polygon_id]]
      for (ring_id in seq_along(rings)) {
        rows[[row_index]] <- ring_to_frame(
          rings[[ring_id]],
          feature_id,
          polygon_id,
          ring_id
        )
        row_index <- row_index + 1
      }
    }
  }

  bind_rows(rows)
}

leg_coordinates <- function(leg) {
  coordinates <- NULL
  if (
    !is.null(leg$geometry) &&
      identical(leg$geometry$type, "LineString") &&
      length(leg$geometry$coordinates)
  ) {
    coordinates <- leg$geometry$coordinates
  } else if (!is.null(leg$path) && length(leg$path)) {
    coordinates <- lapply(leg$path, function(point) {
      list(point$lon, point$lat)
    })
  }

  if (is.null(coordinates) || !length(coordinates)) {
    return(tibble())
  }

  matrix_coords <- do.call(rbind, lapply(coordinates, function(point) {
    as.numeric(unlist(point))
  }))
  if (is.null(dim(matrix_coords)) || ncol(matrix_coords) < 2) {
    return(tibble())
  }

  tibble(
    lon = matrix_coords[, 1],
    lat = matrix_coords[, 2]
  )
}

load_route <- function(case_id, artifact) {
  route_path <- file.path(
    route_dir,
    paste0(case_id, "__", artifact$algorithm_key, ".json")
  )
  route <- read_json_list(route_path)

  legs <- bind_rows(lapply(seq_along(route$legs), function(leg_index) {
    leg_coordinates(route$legs[[leg_index]]) %>%
      mutate(
        leg_id = paste(artifact$algorithm_key, leg_index, sep = "-"),
        leg_index = leg_index
      )
  }))

  if (!nrow(legs)) {
    stop("No route coordinates in: ", route_path)
  }

  list(
    artifact = artifact,
    route = route,
    legs = legs,
    stops = legs %>%
      group_by(leg_id) %>%
      slice_tail(n = 1) %>%
      ungroup(),
    origin = legs %>%
      slice_head(n = 1),
    destination = legs %>%
      slice_tail(n = 1)
  )
}

algorithm_color <- function(algorithm_name) {
  case_when(
    algorithm_name == "Ours" ~ paper_colors$ours,
    algorithm_name == "NSGA-II" ~ paper_colors$reference,
    TRUE ~ paper_colors$accent
  )
}

case_extent <- function(route_objects) {
  all_points <- bind_rows(lapply(route_objects, function(x) x$legs))
  lon_range <- range(all_points$lon, na.rm = TRUE)
  lat_range <- range(all_points$lat, na.rm = TRUE)
  lon_padding <- max(diff(lon_range) * 0.10, 0.008)
  lat_padding <- max(diff(lat_range) * 0.10, 0.006)
  list(
    x = lon_range + c(-lon_padding, lon_padding),
    y = lat_range + c(-lat_padding, lat_padding)
  )
}

route_panel <- function(route_object, geo_frame, extent) {
  artifact <- route_object$artifact
  route_color <- algorithm_color(artifact$algorithm_name)
  elapsed <- as.numeric(artifact$elapsed_ms)
  score <- as.numeric(artifact$primary_metric_value)

  ggplot() +
    geom_polygon(
      data = geo_frame,
      aes(x = lon, y = lat, group = group),
      fill = "#F7F7F7",
      color = "#D7D7D7",
      linewidth = 0.24
    ) +
    geom_path(
      data = route_object$legs,
      aes(x = lon, y = lat, group = leg_id),
      color = route_color,
      linewidth = 1.15,
      lineend = "round",
      linejoin = "round"
    ) +
    geom_point(
      data = route_object$stops,
      aes(x = lon, y = lat),
      shape = 21,
      size = 1.15,
      stroke = 0.42,
      fill = paper_colors$white,
      color = route_color
    ) +
    geom_point(
      data = route_object$origin,
      aes(x = lon, y = lat),
      shape = 21,
      size = 2.65,
      stroke = 0.7,
      fill = paper_colors$reference,
      color = paper_colors$white
    ) +
    geom_point(
      data = route_object$destination,
      aes(x = lon, y = lat),
      shape = 23,
      size = 2.8,
      stroke = 0.7,
      fill = paper_colors$accent,
      color = paper_colors$white
    ) +
    coord_quickmap(
      xlim = extent$x,
      ylim = extent$y,
      expand = FALSE,
      clip = "on"
    ) +
    labs(
      title = artifact$algorithm_name,
      subtitle = paste0(
        "Score ",
        scales::number(score, accuracy = 1, big.mark = ","),
        "  |  ",
        ifelse(
          elapsed >= 1000,
          paste0(scales::number(elapsed / 1000, accuracy = 0.1), " s"),
          paste0(scales::number(elapsed, accuracy = 1), " ms")
        )
      )
    ) +
    theme_paper(base_size = 8.7) +
    theme(
      axis.title = element_blank(),
      axis.text = element_blank(),
      axis.ticks = element_blank(),
      panel.grid = element_blank(),
      plot.title = element_text(
        color = paper_colors$ink,
        size = 9.0,
        face = "bold",
        hjust = 0
      ),
      plot.subtitle = element_text(
        color = paper_colors$muted,
        size = 7.8,
        hjust = 0,
        margin = margin(b = 3)
      ),
      plot.margin = margin(3, 4, 3, 4)
    )
}

manifest <- read_json_list(case_path)
geo_frame <- flatten_geojson(geojson_path)
main_cases <- Filter(
  function(case) identical(case$paper_group, "main"),
  manifest$cases
)

if (length(main_cases) != 2) {
  stop("Expected exactly two main Exp4 cases; found ", length(main_cases))
}

case_components <- function(case, case_letter, comparison_label) {
  route_objects <- lapply(case$artifacts, function(artifact) {
    load_route(case$id, artifact)
  })
  extent <- case_extent(route_objects)
  panels <- lapply(route_objects, route_panel, geo_frame = geo_frame, extent = extent)

  row_title <- paste0(
    "Case ",
    case_letter,
    " - ",
    comparison_label
  )
  row_subtitle <- paste0(
    tools::toTitleCase(gsub("-", " ", case$origin_name)),
    "  |  ",
    sprintf("%02d:%02d", case$depart_time %/% 60, case$depart_time %% 60),
    "  |  ",
    case$budget_minutes / 60,
    "h budget  |  score seed ",
    case$score_seed
  )

  header <- ggplot() +
    annotate(
      "text",
      x = 0,
      y = 0.72,
      label = row_title,
      hjust = 0,
      vjust = 0.5,
      size = 3.7,
      fontface = "bold",
      family = "serif",
      color = paper_colors$ink
    ) +
    annotate(
      "text",
      x = 0,
      y = 0.18,
      label = row_subtitle,
      hjust = 0,
      vjust = 0.5,
      size = 2.75,
      family = "serif",
      color = paper_colors$muted
    ) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1), clip = "off") +
    theme_void() +
    theme(plot.margin = margin(0, 4, 0, 4))

  if (length(panels) != 3) {
    stop("Expected three route panels for ", case$id, "; found ", length(panels))
  }
  list(header = header, panels = panels)
}

a <- case_components(
  main_cases[[1]],
  "A",
  "score and runtime comparison"
)
b <- case_components(
  main_cases[[2]],
  "B",
  "quality-runtime trade-off comparison"
)

# Keep every ggplot at the top level of the patchwork. Nesting each row as a
# separate patchwork can cause some graphics devices to rasterize that row when
# it is embedded in the final PDF.
main_design <- "
AAAAAA
BBCCDD
EEEEEE
FFGGHH
"
main_plot <- a$header +
  a$panels[[1]] +
  a$panels[[2]] +
  a$panels[[3]] +
  b$header +
  b$panels[[1]] +
  b$panels[[2]] +
  b$panels[[3]] +
  plot_layout(
    design = main_design,
    heights = c(0.16, 1, 0.16, 1)
  )

save_paper_plot(
  main_plot,
  file.path(figure_dir, "exp4_main_cases"),
  width = 7.15,
  height = 5.45
)

message("Wrote unified Exp4 figure to: ", figure_dir)
