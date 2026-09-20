"""Вихідний адаптер — читання рецептів із CSV-файлу набору Food.com."""

from ingest_service.application.ports.outbound.recipe_source_port import RecipeSourcePort
from ingest_service.domain.raw_recipe import RawRecipe


class CsvRecipeSource(RecipeSourcePort):
    """Реалізує RecipeSourcePort для файлу RAW_recipes.csv.

    Особливості набору, які треба врахувати:
    - колонки tags, ingredients, steps, nutrition містять рядки виду "['a', 'b']",
      їх треба розібрати в списки (ast.literal_eval);
    - файл великий (~230 тис. рядків), тому читати його потоково, а не весь у пам'ять;
    - після кінця файлу почати спочатку, додаючи до id номер проходу (r-123-2),
      щоб повторні записи не перезаписували старі.
    """

    def __init__(self, csv_path: str) -> None:
        self._csv_path = csv_path

    async def next_batch(self, size: int) -> list[RawRecipe]:
        raise NotImplementedError
