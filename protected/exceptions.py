class SpeciesUnknownError(Exception):

    def __init__(self, species, message="These species were not found in SpeciesNames dictionary"):
        self.species = species
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.species} --> {self.message}'
