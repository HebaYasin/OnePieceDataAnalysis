import unittest

import pandas as pd

from src.cleaning import clean_episode_scripts


class CleanEpisodeScriptsTests(unittest.TestCase):
    def test_removes_repeated_blocks_and_cleans_subtitle_text(self) -> None:
        scripts = pd.Series(
            [
                "♪ Opening song ♪\\NGold Roger-san spoke.\\N"
                "The treasure is out there.\\NThe crew set sail now.\\N"
                "Goodbye, Luffy-sama! Episode 12 {\\i1}\\NSanji shouts, --San--!",
                "♪ Opening song ♪\\NGold Roger-san spoke.\\N"
                "The treasure is out there.\\NThe crew set sail now.\\N"
                "Goodbye, Zoro-kun! Episode 13 {\\i1}",
                "♪ Opening song ♪\\NGold Roger-san spoke.\\N"
                "The treasure is out there.\\NThe crew set sail now.\\N"
                "Goodbye, Nami-chan! Episode 14 {\\i1}",
            ],
            index=[1, 2, 3],
            name="Script",
        )

        cleaned = clean_episode_scripts(scripts, min_repeat_episodes=3)

        self.assertEqual(cleaned.index.tolist(), [1, 2, 3])
        self.assertEqual(
            cleaned.tolist(),
            [
                "Goodbye, Luffy! Sanji shouts, --San--!",
                "Goodbye, Zoro!",
                "Goodbye, Nami!",
            ],
        )
        self.assertEqual(cleaned.name, "Script")

    def test_keeps_unrepeated_dialogue_and_does_not_mutate_input(self) -> None:
        scripts = pd.Series(
            [
                "Luffy-san says hello.\\NThe crew found a hidden island.",
                "Zoro-sama answers.\\NThe crew found a hidden island.",
            ]
        )
        original = scripts.copy()

        cleaned = clean_episode_scripts(scripts)

        self.assertEqual(scripts.tolist(), original.tolist())
        self.assertEqual(cleaned.tolist(), [
            "Luffy says hello. The crew found a hidden island.",
            "Zoro answers. The crew found a hidden island.",
        ])

    def test_rejects_invalid_thresholds(self) -> None:
        with self.assertRaises(ValueError):
            clean_episode_scripts(pd.Series(["script"]), min_repeat_fraction=0)


if __name__ == "__main__":
    unittest.main()
