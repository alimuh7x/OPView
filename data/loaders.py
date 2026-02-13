"""
Legacy data loaders for TextData files.

Contains loaders for CSV-style text data files from the TextData directory.
"""

from pathlib import Path
from typing import Optional, Dict, List, Any
import numpy as np


class LegacyDataLoader:
    """
    Loads legacy CSV-style TextData files.

    Provides backward compatibility with the original data loading
    functions while encapsulating the logic in a reusable class.
    """

    def __init__(self, data_dir: Path):
        """
        Initialize legacy data loader.

        Args:
            data_dir: Directory containing TextData files
        """
        self.data_dir = Path(data_dir)

        # File paths
        self.size_details_file = self.data_dir / "SizeDetails.dat"
        self.size_average_file = self.data_dir / "SizeAveInfo.dat"
        self.stress_strain_file = self.data_dir / "StressStrainFile.txt"
        self.crss_file = self.data_dir / "CRSSFile.txt"
        self.plastic_strain_file = self.data_dir / "PlasticStrainFile.txt"

    def load_size_details(self) -> Optional[Dict[str, Any]]:
        """
        Load grain size details data.

        Returns:
            Dictionary with keys: times, counts, labels, values
            None if file doesn't exist or has no valid data
        """
        if not self.size_details_file.exists():
            return None

        rows = []
        try:
            with self.size_details_file.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    try:
                        rows.append([float(p) for p in parts])
                    except ValueError:
                        continue
        except OSError:
            return None

        if not rows:
            return None

        # Determine columns: first is time, second often count, rest are values
        has_count = len(rows[0]) > 2
        values_offset = 2 if has_count else 1
        labels = [str(idx + 1) for idx in range(len(rows[0]) - values_offset)]
        data_matrix = [row[values_offset:] for row in rows]
        times = [row[0] for row in rows]
        counts = [row[1] for row in rows] if has_count else None

        return {
            "times": times,
            "counts": counts,
            "labels": labels,
            "values": data_matrix,
        }

    def load_size_averages(self) -> Optional[Dict[str, List[float]]]:
        """
        Load grain size averages data.

        Returns:
            Dictionary with keys: times, averages
            None if file doesn't exist or has no valid data
        """
        if not self.size_average_file.exists():
            return None

        times = []
        averages = []

        try:
            with self.size_average_file.open() as fh:
                for line in fh:
                    parts = line.strip().split()
                    if len(parts) < 3:
                        continue
                    try:
                        times.append(float(parts[0]))
                        averages.append(float(parts[2]))
                    except ValueError:
                        continue
        except OSError:
            return None

        if not times:
            return None

        return {"times": times, "averages": averages}

    def load_stress_strain(self) -> Optional[Dict[str, Any]]:
        """
        Load stress-strain data from StressStrainFile.txt.

        Returns:
            Dictionary with keys: strain, time, components, strain_components
            None if file doesn't exist or has no valid data
        """
        if not self.stress_strain_file.exists():
            return None

        try:
            with self.stress_strain_file.open() as fh:
                lines = [line.strip() for line in fh if line.strip()]
        except OSError:
            return None

        if not lines:
            return None

        header = [token.strip() for token in lines[0].replace(',', ' ').split()]
        rows = []

        for line in lines[1:]:
            parts = [token.strip() for token in line.replace(',', ' ').split()]
            if len(parts) != len(header):
                continue
            try:
                rows.append([float(p) for p in parts])
            except ValueError:
                continue

        if not rows:
            return None

        columns = {name: [row[idx] for row in rows] for idx, name in enumerate(header)}

        def col(*names):
            """Helper to get first matching column."""
            for name in names:
                if name in columns:
                    return columns[name]
            return None

        # Extract strain components
        strain_components = {
            name: columns[name]
            for name in columns
            if name.lower().startswith('epsilon')
        }

        strain = strain_components.get('Epsilon_xx') or strain_components.get('EpsilonXX')
        if strain is None and strain_components:
            strain = next(iter(strain_components.values()))

        # Extract time and stress components
        time = col('Time', 'TimeStep')
        sigma_xx = col('Sigma_xx', 'SigmaXX')
        sigma_yy = col('Sigma_yy', 'SigmaYY')
        sigma_zz = col('Sigma_zz', 'SigmaZZ')
        mises = col('Mises', 'VonMises')

        stress_components = {
            key: value for key, value in {
                "Sigma_xx": sigma_xx,
                "Sigma_yy": sigma_yy,
                "Sigma_zz": sigma_zz,
                "Mises": mises,
            }.items() if value is not None
        }

        if not strain or not stress_components:
            return None

        return {
            "strain": strain,
            "time": time,
            "components": stress_components,
            "strain_components": strain_components
        }

    def load_crss(self) -> Optional[Dict[str, Any]]:
        """
        Load CRSS (Critical Resolved Shear Stress) data.

        Returns:
            Dictionary with keys: times, averages, series
            None if file doesn't exist or has no valid data
        """
        if not self.crss_file.exists():
            return None

        try:
            with self.crss_file.open() as fh:
                lines = [line.strip() for line in fh if line.strip()]
        except OSError:
            return None

        if not lines:
            return None

        header = [h.strip() for h in lines[0].split(',')]
        if 'Time' not in header:
            return None

        times = []
        averages = []
        time_idx = header.index('Time')
        avg_idx = header.index('Average') if 'Average' in header else None

        slip_columns = [
            (idx, name)
            for idx, name in enumerate(header)
            if name.lower().startswith('ss_')
        ]

        series = {name: [] for _, name in slip_columns}

        for line in lines[1:]:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) <= time_idx:
                continue

            try:
                time_val = float(parts[time_idx])
            except ValueError:
                continue

            if avg_idx is not None and len(parts) > avg_idx:
                try:
                    avg_val = float(parts[avg_idx])
                except ValueError:
                    avg_val = None
            else:
                avg_val = None

            row_series = {}
            for idx, name in slip_columns:
                if idx >= len(parts):
                    row_series = {}
                    break
                try:
                    row_series[name] = float(parts[idx])
                except ValueError:
                    row_series = {}
                    break

            if not row_series:
                continue

            if avg_val is None:
                avg_val = float(np.mean(list(row_series.values())))

            times.append(time_val)
            averages.append(avg_val)
            for name in series:
                series[name].append(row_series[name])

        if not times:
            return None

        return {"times": times, "averages": averages, "series": series}

    def load_plastic_strain(self) -> Optional[Dict[str, Any]]:
        """
        Load plastic strain data.

        Returns:
            Dictionary with keys: times, epsilons, rates
            None if file doesn't exist or has no valid data
        """
        if not self.plastic_strain_file.exists():
            return None

        try:
            with self.plastic_strain_file.open() as fh:
                lines = [line.strip() for line in fh if line.strip()]
        except OSError:
            return None

        if not lines:
            return None

        header = [token.strip() for token in lines[0].replace(',', ' ').split()]
        rows = []

        for line in lines[1:]:
            parts = [token.strip() for token in line.replace(',', ' ').split()]
            if len(parts) != len(header):
                continue
            try:
                rows.append([float(p) for p in parts])
            except ValueError:
                continue

        if not rows:
            return None

        columns = {name: [row[idx] for row in rows] for idx, name in enumerate(header)}

        def collect(prefix):
            """Collect columns matching prefix."""
            return {
                name: columns[name]
                for name in columns
                if name.lower().startswith(prefix)
            }

        times = columns.get('time') or columns.get('Time')
        if not times:
            return None

        epsilons = collect('epsilon')
        if 'PEEQ' in columns:
            epsilons['PEEQ'] = columns['PEEQ']

        rates = collect('rate')

        return {
            "times": times,
            "epsilons": epsilons,
            "rates": rates
        }

    def load_all(self) -> Dict[str, Optional[Dict]]:
        """
        Load all available data files.

        Returns:
            Dictionary mapping data type names to loaded data
        """
        return {
            'size_details': self.load_size_details(),
            'size_averages': self.load_size_averages(),
            'stress_strain': self.load_stress_strain(),
            'crss': self.load_crss(),
            'plastic_strain': self.load_plastic_strain(),
        }
