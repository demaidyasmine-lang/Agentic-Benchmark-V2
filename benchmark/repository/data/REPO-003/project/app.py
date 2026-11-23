def normalize_name(name):
    # Supprimer les espaces au début et à la fin
    name = name.strip()
    # Convertir en minuscules
    name = name.lower()
    # Remplacer toute suite d'espaces entre les mots par un seul tiret (-)
    name = "-".join(name.split())
    return name