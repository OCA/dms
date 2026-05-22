# Copyright 2026 ledoent — Don Kendall
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# Tests the live-aggregation dashboard contract:
#   - dms.directory.get_dashboard_stats() returns 30-day daily sparklines,
#     24-hour hourly sparkline, and 7-day deltas
#   - dms.file._compute_path() builds a slash-joined path including the file's
#     own filename at the end
#
# Both are pure-functional reads — no fixtures beyond a small file tree.

from .common import StorageDatabaseBaseCase


class TestDashboardStats(StorageDatabaseBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Seed a second file in the same directory so we have >1 file for
        # the sparkline / size aggregation assertions.
        cls.file_2 = cls.create_file(directory=cls.directory)

    def test_returns_expected_keys(self):
        # The shape contract is what the OWL DmsStatBar consumes. Adding a
        # new key is fine; removing one breaks the rendered tile.
        stats = self.directory_model.get_dashboard_stats()
        expected = {
            "files_total",
            "storage_total_bytes",
            "storage_total_human",
            "new_today",
            "files_sparkline",
            "storage_sparkline",
            "new_today_sparkline",
            "files_delta_week",
            "storage_delta_week_human",
            "new_today_avg_per_day",
        }
        self.assertTrue(
            expected.issubset(stats.keys()),
            f"missing keys: {expected - set(stats.keys())}",
        )

    def test_sparkline_lengths_match_window(self):
        stats = self.directory_model.get_dashboard_stats()
        # 30-day daily window → 30 buckets each for files + storage.
        self.assertEqual(len(stats["files_sparkline"]), 30)
        self.assertEqual(len(stats["storage_sparkline"]), 30)
        # 24-hour hourly window → 24 buckets.
        self.assertEqual(len(stats["new_today_sparkline"]), 24)

    def test_files_total_matches_search_count(self):
        # Stats should agree with a direct search_count — they're both
        # under the same ir.rule access. If they diverge we have a hidden
        # filter in the dashboard method.
        stats = self.directory_model.get_dashboard_stats()
        direct = self.file_model.search_count([])
        self.assertEqual(stats["files_total"], direct)

    def test_storage_total_aggregates_size_field(self):
        stats = self.directory_model.get_dashboard_stats()
        # storage_total_bytes is computed via _read_group("size:sum"); make
        # sure it matches the sum of every readable file's `size` field.
        direct = sum(self.file_model.search([]).mapped("size"))
        self.assertEqual(stats["storage_total_bytes"], int(direct))
        # Human-formatted variant is non-empty + has a unit suffix.
        self.assertTrue(stats["storage_total_human"])

    def test_sparkline_today_bucket_has_newly_created_files(self):
        # Both seeded files were created in `setUpClass` → today's daily
        # bucket (index 29, the last in the 30-day window) must be ≥ the
        # number of files we just created.
        stats = self.directory_model.get_dashboard_stats()
        today_count = stats["files_sparkline"][-1]
        # Allow ≥2 in case other tests in the same suite created more.
        self.assertGreaterEqual(today_count, 2)

    def test_delta_week_is_sum_of_last_seven_daily_buckets(self):
        stats = self.directory_model.get_dashboard_stats()
        expected = sum(stats["files_sparkline"][-7:])
        self.assertEqual(stats["files_delta_week"], expected)

    def test_avg_per_day_is_seven_day_average(self):
        stats = self.directory_model.get_dashboard_stats()
        expected = round(sum(stats["files_sparkline"][-7:]) / 7.0, 1)
        self.assertEqual(stats["new_today_avg_per_day"], expected)


class TestComputePath(StorageDatabaseBaseCase):
    def test_root_file_path_includes_root_directory_name(self):
        # `path_names` walks the parent chain back to the storage root —
        # for a file directly under the root directory the shape is
        # "<root_name>/<filename>".
        path = self.file.path_names
        self.assertIn("/", path)
        self.assertTrue(path.endswith(self.file.name))
        self.assertTrue(path.startswith(self.directory.name))

    def test_nested_file_path_includes_full_chain(self):
        # Build a 3-level chain: root → sub → leaf, file under leaf.
        sub = self.directory_model.create(
            {
                "name": "subdir-test",
                "parent_id": self.directory.id,
                "group_ids": [(6, 0, [self.access_group.id])],
            }
        )
        leaf = self.directory_model.create(
            {
                "name": "leafdir-test",
                "parent_id": sub.id,
                "group_ids": [(6, 0, [self.access_group.id])],
            }
        )
        f = self.create_file(directory=leaf)
        # path = "<root>/<sub>/<leaf>/<filename>"
        parts = f.path_names.split("/")
        self.assertEqual(parts[0], self.directory.name)
        self.assertEqual(parts[1], "subdir-test")
        self.assertEqual(parts[2], "leafdir-test")
        self.assertEqual(parts[3], f.name)

    def test_path_json_round_trips_through_json_load(self):
        import json

        chain = json.loads(self.file.path_json)
        # Last entry is the file itself; previous entries are directories.
        self.assertEqual(chain[-1]["model"], "dms.file")
        self.assertEqual(chain[-1]["name"], self.file.name)
        self.assertEqual(chain[0]["model"], "dms.directory")
