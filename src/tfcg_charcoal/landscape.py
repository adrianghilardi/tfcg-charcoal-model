"""Load the five aligned rasters and prepare spatial model inputs."""

from pathlib import Path
import hashlib

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt


INPUT_FILES = {
    "biomass": "InRaster/agb_airdriedMg_ha.tif",
    "reserve": "InRaster/forest_reserve.tif",
    "calendar": "InRaster/harvest_calendar_year.tif",
    "dem": "InRaster/dtem.tif",
    "rivers": "InRaster/rivers.tif",
}


def slope_degrees(elevation, cell_size=25):
    """Maximum absolute slope to the eight neighbours in degrees."""
    xres, yres = (cell_size, cell_size) if np.isscalar(cell_size) else cell_size
    a = np.asarray(elevation, dtype=float)
    padded = np.pad(a, 1, mode="edge")
    maximum = np.zeros(a.shape)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not (dx or dy):
                continue
            other = padded[1 + dy:1 + dy + a.shape[0], 1 + dx:1 + dx + a.shape[1]]
            gradient = np.abs(a - other) / np.hypot(dx * xres, dy * yres)
            maximum = np.fmax(maximum, gradient)
    slope = np.degrees(np.arctan(maximum)).astype(np.float32)
    slope[~np.isfinite(a)] = np.nan
    return slope


def prepare(source):
    """Return reserve-cell vectors and provenance from ``source/InRaster``."""
    source = Path(source).resolve()
    arrays, metadata = {}, {}
    geometry = None
    for name, relative in INPUT_FILES.items():
        path = source / relative
        with rasterio.open(path) as ds:
            current = (ds.shape, ds.crs, ds.transform)
            if geometry is None:
                geometry = current
            elif current != geometry:
                raise ValueError(f"Unaligned raster: {path}")
            if ds.crs is None or not ds.crs.is_projected or ds.crs.linear_units.lower() not in ("metre", "meter"):
                raise ValueError(f"Expected projected coordinates in metres: {path}")
            if ds.transform.b != 0 or ds.transform.d != 0 or ds.transform.a <= 0 or ds.transform.e >= 0:
                raise ValueError(f"Expected a north-up raster without rotation: {path}")
            arrays[name] = ds.read(1, masked=True).astype(float).filled(np.nan)
            metadata[name] = {
                "relative_path": relative,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "valid_cells": int(np.isfinite(arrays[name]).sum()),
                "nodata": ds.nodata,
            }

    shape, crs, transform = geometry
    xres, yres = transform.a, -transform.e
    cell_area_ha = xres * yres / 10_000
    reserve = np.isfinite(arrays["reserve"])
    calendar = arrays["calendar"]
    reporting = reserve & np.isfinite(calendar)
    scheduled_calendar = np.nan_to_num(calendar, nan=0)
    slope = slope_degrees(arrays["dem"], (xres, yres))
    water_distance = np.floor(
        distance_transform_edt(~np.isfinite(arrays["rivers"]), sampling=(yres, xres))
    ).astype(np.int32)

    if not np.all(np.isfinite(arrays["biomass"][reserve])):
        raise ValueError("Biomass is missing within the reserve")
    if not np.all(np.isfinite(slope[reporting])):
        raise ValueError("Elevation is missing within the reporting domain")

    landscape = {
        "initial": (arrays["biomass"][reserve] * cell_area_ha).astype(np.float32),
        "reporting_mask": reporting[reserve],
        "scheduled_year": scheduled_calendar[reserve].astype(np.int32),
        "slope": slope[reserve],
        "water_distance": water_distance[reserve],
        "reserve_mask": reserve,
        "reporting_full_mask": reporting,
    }
    metadata.update(
        crs=str(crs),
        cell_size_m=[xres, yres],
        cell_area_ha=cell_area_ha,
        shape=list(shape),
        transform=list(transform),
        reserve_cells=int(reserve.sum()),
        reporting_cells=int(reporting.sum()),
        reporting_area_ha=float(reporting.sum() * cell_area_ha),
        initial_reporting_biomass_mg=float(np.sum(arrays["biomass"][reporting] * cell_area_ha)),
    )
    return landscape, metadata


def eligibility(landscape, parameters):
    return ~(
        (landscape["water_distance"] < parameters.water_buffer_m)
        | (landscape["slope"] > parameters.max_slope_deg)
    )
