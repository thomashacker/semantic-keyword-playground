"""
Download real dataset content from the Wikipedia REST API.
Usage:
  uv run python -m scripts.download_datasets --dataset all
  uv run python -m scripts.download_datasets --dataset movies --limit 100
"""
import argparse
import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import quote

DATA_DIR = Path(__file__).parent.parent / "data"

LANDMARK_TITLES = [
    "Eiffel Tower", "Colosseum", "Great Wall of China", "Machu Picchu", "Taj Mahal",
    "Acropolis of Athens", "Stonehenge", "Angkor Wat", "Chichen Itza", "Petra",
    "Pyramids of Giza", "Sagrada Familia", "Big Ben", "Statue of Liberty", "Sydney Opera House",
    "Burj Khalifa", "Tower of London", "Alhambra", "Versailles", "Mont Saint-Michel",
    "Hagia Sophia", "Pantheon, Rome", "Parthenon", "Pompeii", "Uffizi Gallery",
    "Vatican Museums", "Louvre Museum", "British Museum", "Metropolitan Museum of Art", "Hermitage Museum",
    "Neuschwanstein Castle", "Prague Castle", "Edinburgh Castle", "Windsor Castle", "Château de Chambord",
    "Château de Chillon", "Bran Castle", "Alcazar of Segovia", "Alhambra", "Pena Palace",
    "Dubrovnik Old Town", "Venice", "Florence", "Santorini", "Amalfi Coast",
    "Cinque Terre", "Cappadocia", "Pamukkale", "Ephesus", "Troy",
    "Göbekli Tepe", "Persepolis", "Babylon", "Ur", "Karnak",
    "Abu Simbel", "Valley of the Kings", "Luxor Temple", "Sphinx", "Giza pyramid complex",
    "Sugarloaf Mountain", "Christ the Redeemer", "Iguazu Falls", "Amazon rainforest", "Galápagos Islands",
    "Machu Picchu", "Nazca Lines", "Easter Island", "Torres del Paine National Park", "Atacama Desert",
    "Niagara Falls", "Grand Canyon", "Yellowstone National Park", "Yosemite National Park", "Monument Valley",
    "Antelope Canyon", "Bryce Canyon National Park", "Zion National Park", "Arches National Park", "Joshua Tree National Park",
    "Mount Rushmore", "Statue of Liberty", "Golden Gate Bridge", "Empire State Building", "One World Trade Center",
    "Space Needle", "Hollywood Sign", "Las Vegas Strip", "Times Square", "Central Park",
    "Great Barrier Reef", "Uluru", "Blue Mountains", "Kakadu National Park", "Twelve Apostles (Victoria)",
    "Milford Sound", "Fiordland National Park", "Bay of Islands", "Waitomo Glowworm Caves", "Tongariro Alpine Crossing",
    "Mount Fuji", "Tokyo Tower", "Fushimi Inari-taisha", "Arashiyama", "Kinkaku-ji",
    "Nijo Castle", "Hiroshima Peace Memorial", "Nara Park", "Sensō-ji", "Tokyo Skytree",
    "Forbidden City", "Temple of Heaven", "Summer Palace", "Terracotta Army", "Li River",
    "Zhangjiajie National Forest Park", "Yellow Mountain", "West Lake", "Guilin", "Zhangye Danxia",
    "Taj Mahal", "Amber Fort", "Lotus Temple", "Ajanta Caves", "Ellora Caves",
    "Hampi", "Khajuraho", "Meenakshi Amman Temple", "Victoria Memorial", "Gateway of India",
    "Bagan", "Borobudur", "Prambanan", "Ha Long Bay", "Hội An Ancient Town",
    "Angkor Wat", "Sigiriya", "Dambulla Cave Temple", "Kandy", "Adam's Peak",
    "Serengeti National Park", "Ngorongoro Crater", "Mount Kilimanjaro", "Victoria Falls", "Okavango Delta",
    "Sahara desert", "Atlas Mountains", "Marrakech", "Fez, Morocco", "Carthage",
    "Timbuktu", "Great Mosque of Djenné", "Valley of the Kings", "Karnak", "Luxor",
    "Petra", "Wadi Rum", "Dead Sea", "Jerusalem Old City", "Masada",
    "Baalbek", "Byblos", "Palmyra", "Pamukkale", "Ephesus",
    "Cappadocia", "Göreme", "Mount Ararat", "Ani", "Nemrut Dağı",
    "Acropolis of Athens", "Delphi", "Olympia, Greece", "Meteora", "Rhodes Old Town",
    "Knossos", "Mycenae", "Epidaurus", "Tikal", "Copán",
    "Teotihuacan", "Monte Albán", "Chichen Itza", "Tulum", "Palenque",
    "Iguazu Falls", "Jesuit Missions of the Guaranis", "Rapa Nui", "Chan Chan", "Tiwanaku",
    "Lascaux", "Altamira", "Stonehenge", "Avebury", "Skara Brae",
    "Newgrange", "Carnac stones", "Callanish Stones", "Ring of Brodgar", "Orkney",
    "Aqueduct of Segovia", "Pont du Gard", "Hadrian's Wall", "Limes Germanicus", "Vindolanda",
    "Château de Fontainebleau", "Palace of Versailles", "Carcassonne", "Vézelay Abbey", "Chartres Cathedral",
    "Notre-Dame de Paris", "Sainte-Chapelle", "Montmartre", "Arc de Triomphe", "Place de la Concorde",
    "Trevi Fountain", "Spanish Steps", "Piazza Navona", "Campo de' Fiori", "Trastevere",
    "Basilica di San Marco", "Doge's Palace", "Rialto Bridge", "Grand Canal", "Murano",
    "Duomo di Milano", "Galleria Vittorio Emanuele II", "Leonardo da Vinci's Last Supper", "Sforzesco Castle", "Navigli",
    "Leaning Tower of Pisa", "Baptistery of Pisa", "Piazza dei Miracoli", "Uffizi Gallery", "Ponte Vecchio",
    "Piazza della Signoria", "Giotto's Campanile", "Florence Cathedral", "Boboli Gardens", "Palazzo Pitti",
    "Trevi Fountain", "Borghese Gallery", "Colosseum", "Forum Romanum", "Palatine Hill",
    "Sistine Chapel", "Saint Peter's Basilica", "Castel Sant'Angelo", "Via Appia Antica", "Catacombs of Rome",
    "Pompeii", "Herculaneum", "Mount Vesuvius", "Amalfi Cathedral", "Positano",
    "Capri", "Ravello", "Paestum", "Alberobello", "Matera",
    "Palermo Cathedral", "Valley of the Temples", "Monreale Cathedral", "Taormina", "Mount Etna",
    "Alhambra", "Córdoba Mosque–Cathedral", "Seville Cathedral", "Casa Batlló", "Park Güell",
    "La Rambla", "Camp Nou", "Montjuïc", "Tibidabo", "Palau de la Música Catalana",
    "Prado Museum", "Royal Palace of Madrid", "Retiro Park", "Puerta del Sol", "Plaza Mayor, Madrid",
    "Sagrada Familia", "Torre Agbar", "Palau Güell", "Barcelona Pavilion", "Barceloneta Beach",
    "Rock of Gibraltar", "Alhambra", "Generalife", "Alcazar of Seville", "Plaza de España, Seville",
    "Buckingham Palace", "Palace of Westminster", "Tower Bridge", "St Paul's Cathedral", "Tate Modern",
    "Natural History Museum, London", "Victoria and Albert Museum", "Science Museum, London", "National Gallery, London", "Trafalgar Square",
    "Covent Garden", "Carnaby Street", "Portobello Road Market", "Camden Market", "Borough Market",
    "Edinburgh Castle", "Royal Mile", "Arthur's Seat", "Holyrood Palace", "Scottish National Gallery",
    "Stonehenge", "Bath, Somerset", "Roman Baths, Bath", "Glastonbury Tor", "Salisbury Cathedral",
    "Canterbury Cathedral", "Dover Castle", "Leeds Castle", "Hever Castle", "Blenheim Palace",
    "Stirling Castle", "Rosslyn Chapel", "Loch Ness", "Glen Coe", "Eilean Donan",
    "Giant's Causeway", "Cliffs of Moher", "Ring of Kerry", "Rock of Cashel", "Newgrange",
    "Skellig Michael", "Trinity College Dublin", "Blarney Castle", "Kilkenny Castle", "Powerscourt Estate",
    "Rijksmuseum", "Van Gogh Museum", "Anne Frank House", "Keukenhof", "Kinderdijk",
    "Bruges historic centre", "Grand Place, Brussels", "Atomium", "Manneken Pis", "Ghent",
    "Cologne Cathedral", "Neuschwanstein Castle", "Rothenburg ob der Tauber", "Heidelberg Castle", "Brandenburg Gate",
    "Berlin Wall", "Museum Island", "Sanssouci", "Checkpoint Charlie", "Potsdamer Platz",
    "Checkpoint Charlie", "Hofbräuhaus", "Nymphenburg Palace", "Marienplatz", "English Garden, Munich",
    "Charles Bridge", "Old Town Square, Prague", "Astronomical Clock, Prague", "St. Vitus Cathedral", "Josefov",
    "Wawel Castle", "Auschwitz concentration camp", "Old Town, Kraków", "Wieliczka Salt Mine", "Malbork Castle",
    "Budapest Parliament Building", "Matthias Church", "Fisherman's Bastion", "Buda Castle", "Chain Bridge",
    "Schönbrunn Palace", "Belvedere (palace)", "St. Stephen's Cathedral, Vienna", "Prater", "Kunsthistorisches Museum",
    "St. Moritz", "Matterhorn", "Jungfraujoch", "Lake Geneva", "Château de Chillon",
    "Mont Blanc", "Chamonix", "Mer de Glace", "Zermatt", "Lauterbrunnen",
    "Fjords of Norway", "Geirangerfjord", "Nærøyfjord", "Northern Lights", "Svalbard",
    "Stockholm Old Town", "Vasa Museum", "ABBA Museum", "Skansen", "Stockholm City Hall",
    "Helsinki Cathedral", "Suomenlinna", "Senate Square, Helsinki", "Temppeliaukio Church", "Kiasma",
    "Kronborg Castle", "Tivoli Gardens", "Rosenborg Castle", "Louisiana Museum of Modern Art", "Roskilde Cathedral",
    "Reykjavik", "Geysir", "Gullfoss", "Blue Lagoon, Iceland", "Þingvellir",
    "Greenland ice sheet", "Ilulissat Icefjord", "Qaqortoq", "Nuuk", "Disko Island",
]

MOVIE_TITLES = [
    "The Godfather", "Blade Runner", "Jurassic Park", "Forrest Gump", "The Matrix",
    "Inception", "Parasite (2019 film)", "Spirited Away", "WALL-E", "Schindler's List",
    "The Shawshank Redemption", "Pulp Fiction", "The Dark Knight", "Goodfellas", "12 Angry Men",
    "Casablanca (film)", "Fight Club (film)", "The Silence of the Lambs (film)", "Interstellar (film)", "Rear Window",
    "The Prestige (film)", "Whiplash (film)", "Gladiator (2000 film)", "The Departed", "Braveheart",
    "City of God (film)", "Apocalypse Now", "Sunset Boulevard (film)", "Mulholland Drive (film)", "2001: A Space Odyssey",
    "Seven Samurai", "The Lord of the Rings: The Fellowship of the Ring", "The Lord of the Rings: The Return of the King",
    "Schindler's List", "Full Metal Jacket", "The Good, the Bad and the Ugly",
    "Once Upon a Time in America", "Cinema Paradiso", "Life Is Beautiful (film)", "Amélie",
    "Pan's Labyrinth", "Oldboy (2003 film)", "Memento (film)", "No Country for Old Men (film)",
    "There Will Be Blood (film)", "The Grand Budapest Hotel", "Moonrise Kingdom", "Knives Out",
    "Get Out (film)", "Us (2019 film)", "Hereditary (film)", "Midsommar (film)", "A Quiet Place (film)",
    "Bird Box (film)", "It (2017 film)", "Joker (2019 film)", "1917 (film)", "Ford v Ferrari",
    "Parasite (2019 film)", "Avengers: Endgame", "Avengers: Infinity War", "Black Panther (film)", "Spider-Man: No Way Home",
    "Top Gun: Maverick", "The Batman (film)", "Everything Everywhere All at Once", "Oppenheimer (film)", "Barbie (film)",
    "Dune (2021 film)", "The Irishman", "Marriage Story (film)", "Little Women (2019 film)", "Uncut Gems",
    "Portrait of a Lady on Fire", "Parasite (2019 film)", "Bong Joon-ho", "La La Land", "Whiplash (film)",
    "Mad Max: Fury Road", "The Revenant (film)", "Spotlight (film)", "The Big Short (film)", "Room (2015 film)",
    "Brooklyn (film)", "The Martian (film)", "Ex Machina (film)", "Boyhood (film)", "Birdman (film)",
    "Her (film)", "Nebraska (film)", "American Hustle (film)", "Gravity (film)", "12 Years a Slave (film)",
    "Django Unchained", "Lincoln (film)", "Argo (film)", "Zero Dark Thirty", "Les Misérables (2012 film)",
    "Silver Linings Playbook", "Beasts of the Southern Wild", "The Artist (film)", "The Tree of Life (film)", "Midnight in Paris",
    "Black Swan (film)", "The Social Network (film)", "Inception", "The King's Speech", "127 Hours (film)",
    "Winter's Bone (film)", "True Grit (2010 film)", "The Fighter (film)", "Blue Valentine (film)", "Black Swan (film)",
    "A Separation (film)", "The Artist (film)", "The Descendants (film)", "Moneyball (film)", "War Horse (film)",
    "Hugo (film)", "The Girl with the Dragon Tattoo (2011 film)", "Drive (2011 film)", "Midnight in Paris", "Tree of Life (film)",
    "Toy Story", "Toy Story 2", "Toy Story 3", "Toy Story 4", "Finding Nemo",
    "Finding Dory", "Inside Out (film)", "Up (film)", "Coco (film)", "Brave (film)",
    "The Incredibles", "Ratatouille (film)", "WALL-E", "Monsters, Inc.", "A Bug's Life",
    "Cars (film)", "Monsters University", "The Good Dinosaur", "Onward (film)", "Soul (film)",
    "Luca (film)", "Turning Red", "Lightyear (film)", "Elemental (film)", "Wish (film)",
    "Frozen (film)", "Frozen II", "Moana (film)", "Encanto (film)", "Zootopia",
    "Big Hero 6 (film)", "Wreck-It Ralph", "Ralph Breaks the Internet", "Bolt (film)", "Tangled",
    "The Princess and the Frog", "Pocahontas (film)", "Mulan (1998 film)", "Tarzan (1999 film)", "Fantasia (film)",
    "Snow White and the Seven Dwarfs (1937 film)", "Cinderella (1950 film)", "Sleeping Beauty (1959 film)", "The Little Mermaid (1989 film)", "Beauty and the Beast (1991 film)",
    "Aladdin (1992 film)", "The Lion King", "The Jungle Book (1967 film)", "Bambi (film)", "Dumbo (1941 film)",
    "Pinocchio (1940 film)", "Peter Pan (1953 film)", "Alice in Wonderland (1951 film)", "Fantasia 2000", "Treasure Planet",
    "Atlantis: The Lost Empire", "The Emperor's New Groove", "Lilo & Stitch", "Brother Bear (film)", "Home on the Range (film)",
    "Chicken Little (film)", "Meet the Robinsons (film)", "The Princess and the Frog", "Tangled", "Winnie the Pooh (2011 film)",
    "Shrek", "Shrek 2", "Shrek the Third", "Shrek Forever After", "Puss in Boots (film)",
    "Madagascar (film)", "Madagascar: Escape 2 Africa", "Madagascar 3: Europe's Most Wanted", "Kung Fu Panda", "Kung Fu Panda 2",
    "Kung Fu Panda 3", "How to Train Your Dragon", "How to Train Your Dragon 2", "The Croods", "The Croods: A New Age",
    "Trolls (film)", "Boss Baby", "Captain Underpants: The First Epic Movie", "Abominable (film)", "The Bad Guys (film)",
    "Star Wars: Episode IV – A New Hope", "Star Wars: Episode V – The Empire Strikes Back", "Star Wars: Episode VI – Return of the Jedi",
    "Star Wars: Episode I – The Phantom Menace", "Star Wars: Episode II – Attack of the Clones",
    "Star Wars: Episode III – Revenge of the Sith", "Star Wars: The Force Awakens", "Star Wars: The Last Jedi",
    "Star Wars: The Rise of Skywalker", "Rogue One: A Star Wars Story",
    "Solo: A Star Wars Story", "The Avengers (2012 film)", "Iron Man (film)", "Captain America: The First Avenger",
    "Thor (film)", "The Incredible Hulk (film)", "Captain America: The Winter Soldier", "Guardians of the Galaxy (film)",
    "Avengers: Age of Ultron", "Ant-Man (film)", "Captain America: Civil War", "Doctor Strange (film)",
    "Guardians of the Galaxy Vol. 2", "Thor: Ragnarok", "Black Panther (film)", "Avengers: Infinity War",
    "Ant-Man and the Wasp", "Captain Marvel (film)", "Avengers: Endgame", "Spider-Man: Far From Home",
    "Black Widow (film)", "Shang-Chi and the Legend of the Ten Rings", "Eternals (film)", "Spider-Man: No Way Home",
    "Doctor Strange in the Multiverse of Madness", "Thor: Love and Thunder", "Black Panther: Wakanda Forever",
    "Ant-Man and the Wasp: Quantumania", "Guardians of the Galaxy Vol. 3", "The Marvels (film)",
    "Batman (1989 film)", "Batman Returns", "Batman Forever", "Batman & Robin (film)", "Batman Begins",
    "The Dark Knight", "The Dark Knight Rises", "Batman v Superman: Dawn of Justice",
    "Man of Steel (film)", "Wonder Woman (2017 film)", "Aquaman (film)", "Shazam! (film)",
    "Birds of Prey (film)", "Suicide Squad (film)", "The Suicide Squad (film)", "Black Adam (film)",
    "The Flash (film)", "Aquaman and the Lost Kingdom", "Blue Beetle (film)", "Joker (2019 film)",
    "Raiders of the Lost Ark", "Indiana Jones and the Temple of Doom", "Indiana Jones and the Last Crusade",
    "Indiana Jones and the Kingdom of the Crystal Skull", "Indiana Jones and the Dial of Destiny",
    "Back to the Future", "Back to the Future Part II", "Back to the Future Part III",
    "Die Hard", "Die Hard 2", "Die Hard with a Vengeance", "Terminator (franchise)", "The Terminator",
    "Terminator 2: Judgment Day", "Terminator 3: Rise of the Machines", "Terminator Salvation", "Terminator Genisys",
    "RoboCop", "Total Recall (1990 film)", "Basic Instinct", "Se7en", "Heat (1995 film)",
    "L.A. Confidential (film)", "Boogie Nights (film)", "Magnolia (film)", "Eyes Wide Shut",
    "American Beauty (film)", "Traffic (film)", "Almost Famous", "The Hours (film)",
    "Chicago (2002 film)", "Gangs of New York", "The Hours (film)", "Adaptation (film)",
    "The Royal Tenenbaums", "Punch-Drunk Love", "Minority Report (film)", "Catch Me If You Can",
    "Gangs of New York", "25th Hour", "Lost in Translation (film)", "Mystic River",
    "Master and Commander: The Far Side of the World", "Big Fish (film)", "Kill Bill: Volume 1",
    "Kill Bill: Volume 2", "Eternal Sunshine of the Spotless Mind", "Sideways (film)",
    "Million Dollar Baby", "The Aviator (film)", "Crash (2004 film)", "Capote (film)",
    "Brokeback Mountain", "Munich (film)", "Good Night, and Good Luck", "A History of Violence",
    "The New World (film)", "Match Point (film)", "Walk the Line (film)", "Syriana",
    "Grizzly Man", "A Scanner Darkly (film)", "Children of Men (film)", "Pan's Labyrinth",
    "The Queen (2006 film)", "Babel (film)", "Letters from Iwo Jima", "The Departed",
    "Blood Diamond (film)", "Casino Royale (2006 film)", "Borat (film)",
    "United 93 (film)", "The Pursuit of Happyness", "The Prestige (film)", "The Science of Sleep",
    "Half Nelson (film)", "Thank You for Smoking (film)", "Me and You and Everyone We Know",
    "Squid Game", "Parasite (2019 film)", "The Handmaid's Tale (TV series)", "Black Mirror", "Dark (TV series)",
    "Stranger Things", "The Crown (TV series)", "Chernobyl (miniseries)", "Band of Brothers (miniseries)",
    "Game of Thrones", "Breaking Bad", "The Wire", "The Sopranos", "Twin Peaks",
    "True Detective", "Fargo (TV series)", "Mindhunter (TV series)", "Narcos (TV series)", "Ozark (TV series)",
    "Succession (TV series)", "Fleabag", "Atlanta (TV series)", "Barry (TV series)", "Ted Lasso",
    "The Bear (TV series)", "White Lotus", "Severance (TV series)", "Yellowjackets", "Euphoria (TV series)",
    "Squid Game", "Squid Game: The Challenge",
]

SCIENCE_TITLES = [
    "Photosynthesis", "Black hole", "DNA", "Evolution", "General relativity",
    "Quantum mechanics", "Natural selection", "Big Bang", "Mitosis", "Entropy",
    "String theory", "Electromagnetic radiation", "Plate tectonics", "Immune system", "Stem cell",
    "CRISPR", "Artificial intelligence", "Machine learning", "Neural network", "Deep learning",
    "Neutrino", "Higgs boson", "Dark matter", "Dark energy", "Cosmic microwave background",
    "Standard Model", "Gravitational wave", "Supernova", "Neutron star", "Black hole information paradox",
    "Schrödinger equation", "Uncertainty principle", "Wave–particle duality", "Quantum entanglement", "Quantum computing",
    "Transistor", "Semiconductor", "Integrated circuit", "Laser", "Fiber optics",
    "Internet", "World Wide Web", "GPS", "Blockchain", "Cryptography",
    "Protein folding", "Enzyme", "Ribosome", "Mitochondria", "Cell membrane",
    "Nervous system", "Brain", "Neuron", "Synapse", "Neuroplasticity",
    "Genome", "Gene", "Chromosome", "Epigenetics", "Genomics",
    "Metabolism", "Photon", "Electron", "Proton", "Neutron",
    "Atom", "Molecule", "Chemical bond", "Periodic table", "Thermodynamics",
    "Conservation of energy", "Gravity", "Electric field", "Magnetic field", "Electromagnetism",
    "Wave", "Sound", "Light", "Optics", "Lens",
    "Solar system", "Planet", "Moon", "Asteroid", "Comet",
    "Galaxy", "Milky Way", "Star", "Sun", "Exoplanet",
    "Telescope", "Hubble Space Telescope", "James Webb Space Telescope", "Space Shuttle", "Apollo program",
    "Mars", "Jupiter", "Saturn", "Venus", "Mercury (planet)",
    "Atmosphere", "Climate change", "Greenhouse effect", "Carbon dioxide", "Ozone layer",
    "Photovoltaic system", "Nuclear fusion", "Nuclear fission", "Radioactivity", "Isotope",
    "Superconductivity", "Plasma (physics)", "Condensed matter physics", "Nanotechnology", "Biomimetics",
    "Vaccination", "Antibiotic", "Virus", "Bacteria", "Prion",
    "Cancer", "HIV/AIDS", "Alzheimer's disease", "Parkinson's disease", "Diabetes",
    "Heart", "Lung", "Liver", "Kidney", "Blood",
    "Oxygen", "Hydrogen", "Carbon", "Nitrogen", "Iron",
    "Water", "Salt (chemistry)", "Acid", "Base (chemistry)", "pH",
    "Osmosis", "Diffusion", "Capillary action", "Surface tension", "Viscosity",
    "Aerodynamics", "Fluid dynamics", "Turbulence", "Chaos theory", "Fractal",
    "Statistics", "Probability", "Game theory", "Information theory", "Cryptography",
    "Number theory", "Calculus", "Algebra", "Geometry", "Topology",
    "Fibonacci sequence", "Prime number", "Pi", "Infinity", "Complex number",
    "Ecosystem", "Food chain", "Biodiversity", "Extinction", "Invasive species",
    "Coral reef", "Rainforest", "Tundra", "Desert", "Ocean",
    "Earthquake", "Volcano", "Tsunami", "Hurricane", "Tornado",
    "Glacier", "Sea level rise", "Permafrost", "Deforestation", "Pollution",
    "Renewable energy", "Wind power", "Hydroelectricity", "Geothermal energy", "Biofuel",
    "Electric vehicle", "Battery", "Fuel cell", "Hydrogen economy", "Carbon capture",
    "Fermentation", "Distillation", "Chromatography", "Spectroscopy", "Mass spectrometry",
    "MRI", "CT scan", "Ultrasound", "X-ray", "Positron emission tomography",
    "Gene therapy", "Stem cell therapy", "Organ transplantation", "Dialysis", "Chemotherapy",
    "Antibiotic resistance", "Zoonosis", "Pandemic", "Epidemiology", "Herd immunity",
    "Psychology", "Cognitive science", "Behavioral economics", "Placebo effect", "Cognitive bias",
    "Dopamine", "Serotonin", "Cortisol", "Oxytocin", "Melatonin",
    "Sleep", "Dream", "Memory", "Consciousness", "Intelligence",
    "Language", "Speech", "Writing", "Mathematics", "Logic",
    "Philosophy of mind", "Free will", "Determinism", "Emergence", "Complexity",
    "Abiogenesis", "Astrobiology", "Fermi paradox", "Drake equation", "SETI",
    "Cryonics", "Life extension", "Transhumanism", "Genetic engineering", "Synthetic biology",
    "Robotics", "Automation", "Internet of Things", "Cloud computing", "Virtual reality",
    "Augmented reality", "Brain–computer interface", "Exoskeleton", "Prosthetics", "Bioprinting",
    "Materials science", "Graphene", "Carbon nanotube", "Metamaterial", "Piezoelectricity",
    "Photovoltaics", "OLED", "LCD", "MEMS", "Microfluidics",
    "Chemical element", "Alloy", "Polymer", "Ceramic", "Composite material",
    "Magnetism", "Diamagnetism", "Ferromagnetism", "Spintronics", "Quantum Hall effect",
    "Bose–Einstein condensate", "Superfluidity", "Superconductor", "Josephson junction", "Quantum dot",
    "Photoelectric effect", "Compton scattering", "Pair production", "Antimatter", "Positron",
    "Cyclotron", "Particle accelerator", "Large Hadron Collider", "Synchrotron", "Free-electron laser",
    "Neuroscience", "Cognitive neuroscience", "Connectome", "Optogenetics", "Neuroprosthetics",
    "Microbiome", "Gut flora", "Probiotic", "Pathogen", "Parasitology",
    "Endocrinology", "Homeostasis", "Feedback (biology)", "Allostasis", "Thermoregulation",
    "Cell division", "Apoptosis", "Cell signaling", "Receptor (biochemistry)", "Ligand",
    "Transcription (biology)", "Translation (biology)", "Post-translational modification", "Protein structure", "Proteomics",
    "Bioinformatics", "Computational biology", "Systems biology", "Network biology", "Evolutionary biology",
    "Paleontology", "Fossil", "Geological time scale", "Cambrian explosion", "Mass extinction",
    "Dinosaur", "Human evolution", "Homo sapiens", "Neanderthal", "Hominidae",
    "Taxonomy (biology)", "Binomial nomenclature", "Phylogenetics", "Cladistics", "Convergent evolution",
    "Symbiosis", "Mutualism (biology)", "Parasitism", "Predation", "Competition (biology)",
    "Habitat", "Niche (ecology)", "Carrying capacity", "Population dynamics", "Biomass",
    "Nitrogen cycle", "Carbon cycle", "Water cycle", "Phosphorus cycle", "Oxygen cycle",
    "Deforestation", "Habitat destruction", "Climate change", "Ocean acidification", "Eutrophication",
    "Endangered species", "Conservation biology", "Wildlife corridor", "Reforestation", "Rewilding",
    "Hydraulics", "Pneumatics", "Tribology", "Fracture mechanics", "Fatigue (material)",
    "Corrosion", "Welding", "Casting (metalworking)", "Forging", "Machining",
    "Civil engineering", "Structural engineering", "Geotechnical engineering", "Hydraulic engineering", "Environmental engineering",
    "Thermodynamics", "Heat transfer", "Mass transfer", "Chemical kinetics", "Catalysis",
    "Electrochemistry", "Electroplating", "Electrolysis", "Galvanic cell", "Fuel cell",
    "Spectroscopy", "Nuclear magnetic resonance", "Infrared spectroscopy", "Raman spectroscopy", "X-ray crystallography",
    "Microscopy", "Electron microscope", "Scanning tunneling microscope", "Atomic force microscope", "Confocal microscopy",
    "Flow cytometry", "Polymerase chain reaction", "DNA sequencing", "Gel electrophoresis", "Western blot",
    "ELISA", "Immunofluorescence", "In situ hybridization", "Cloning", "Transfection",
    "Animal testing", "Clinical trial", "Randomized controlled trial", "Meta-analysis", "Systematic review",
    "Bayesian inference", "Frequentist statistics", "Hypothesis testing", "P-value", "Confidence interval",
    "Mathematical model", "Simulation", "Monte Carlo method", "Finite element method", "Agent-based model",
    "Graph theory", "Linear algebra", "Differential equation", "Fourier transform", "Wavelet",
    "Cryptography", "Public-key cryptography", "Hash function", "Digital signature", "Zero-knowledge proof",
    "Algorithm", "Data structure", "Computational complexity theory", "P versus NP problem", "Turing machine",
    "Formal language", "Regular expression", "Compiler", "Operating system", "Distributed computing",
    "Parallel computing", "Graphics processing unit", "Field-programmable gate array", "Application-specific integrated circuit", "Quantum computing",
]


def fetch_wikipedia_summary(title: str) -> dict | None:
    """Fetch the Wikipedia summary for a given title."""
    encoded = quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    req = Request(url, headers={"User-Agent": "semantic-search-playground/1.0 (educational)"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("type") == "disambiguation":
                return None
            extract = data.get("extract", "").strip()
            if not extract:
                return None
            return {"title": data.get("title", title), "extract": extract}
    except HTTPError as e:
        if e.code == 404:
            return None
        print(f"  HTTP {e.code} for: {title}")
        return None
    except (URLError, Exception) as e:
        print(f"  Error for '{title}': {e}")
        return None


def download_landmarks(limit: int) -> list[dict]:
    titles = LANDMARK_TITLES[:limit]
    results = []
    seen = set()
    for title in titles:
        data = fetch_wikipedia_summary(title)
        if data and data["title"].lower() not in seen:
            seen.add(data["title"].lower())
            results.append({
                "title": data["title"],
                "description": data["extract"][:500],
                "country": "",
                "category": "landmark",
            })
            print(f"  + {data['title']}")
        else:
            if not data:
                print(f"  - skip: {title}")
        time.sleep(0.1)
    return results


def download_movies(limit: int) -> list[dict]:
    titles = MOVIE_TITLES[:limit]
    results = []
    seen = set()
    for title in titles:
        data = fetch_wikipedia_summary(title)
        if data and data["title"].lower() not in seen:
            seen.add(data["title"].lower())
            results.append({
                "title": data["title"],
                "plot": data["extract"][:500],
                "genre": "drama",
                "year": 2000,
            })
            print(f"  + {data['title']}")
        else:
            if not data:
                print(f"  - skip: {title}")
        time.sleep(0.1)
    return results


def download_science(limit: int) -> list[dict]:
    titles = SCIENCE_TITLES[:limit]
    results = []
    seen = set()
    for title in titles:
        data = fetch_wikipedia_summary(title)
        if data and data["title"].lower() not in seen:
            seen.add(data["title"].lower())
            results.append({
                "concept": data["title"],
                "explanation": data["extract"][:500],
                "field": "science",
            })
            print(f"  + {data['title']}")
        else:
            if not data:
                print(f"  - skip: {title}")
        time.sleep(0.1)
    return results


def main():
    parser = argparse.ArgumentParser(description="Download Wikipedia summaries for datasets")
    parser.add_argument(
        "--dataset",
        choices=["landmarks", "movies", "science", "all"],
        default="all",
        help="Which dataset to download",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Max number of items to fetch per dataset",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)

    datasets_to_run = (
        ["landmarks", "movies", "science"] if args.dataset == "all" else [args.dataset]
    )

    for ds in datasets_to_run:
        print(f"\nDownloading {ds} (limit={args.limit})...")
        if ds == "landmarks":
            data = download_landmarks(args.limit)
            out = DATA_DIR / "landmarks.json"
        elif ds == "movies":
            data = download_movies(args.limit)
            out = DATA_DIR / "movies.json"
        else:
            data = download_science(args.limit)
            out = DATA_DIR / "science.json"

        with open(out, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Wrote {len(data)} items to {out}")


if __name__ == "__main__":
    main()
