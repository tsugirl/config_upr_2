import json
import os
import xml.etree.ElementTree as ET

def parse_dependencies(pom_path):
    tree = ET.parse(pom_path)
    root = tree.getroot()
    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}

    dependencies = []
    for dependency in root.findall(".//maven:dependency", ns):
        group_id = dependency.find("maven:groupId", ns).text
        artifact_id = dependency.find("maven:artifactId", ns).text
        dependencies.append(f"{group_id}:{artifact_id}")
    return dependencies

def parse_pom_file(pom_path, repository_path, processed=None):
    if processed is None:
        processed = set()
    
    # проверка наличия POM-файла
    if not os.path.exists(pom_path):
        print(f"File not found: {pom_path}")
        return []

    tree = ET.parse(pom_path)
    root = tree.getroot()
    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
    dependencies = []

    # парсинг зависимостей
    for dependency in root.findall(".//maven:dependency", ns):
        group_id = dependency.find("maven:groupId", ns)
        artifact_id = dependency.find("maven:artifactId", ns)
        version = dependency.find("maven:version", ns)

        # проверка на None
        if group_id is None or artifact_id is None:
            continue  # пропускаю, если важные поля отсутствуют

        group_id = group_id.text
        artifact_id = artifact_id.text
        version = version.text if version is not None else "unspecified"

        dependency_key = f"{group_id}:{artifact_id}:{version}"

        if dependency_key not in processed:
            processed.add(dependency_key)
            dependencies.append(dependency_key)

            # путь к POM-файлу зависимости
            dependency_pom_path = os.path.join(
                repository_path,
                group_id.replace('.', '/'),
                artifact_id,
                version,
                f"{artifact_id}-{version}.pom"
            )

            # рекурсивный вызов для парсинга транзитивных зависимостей
            if os.path.exists(dependency_pom_path):
                dependencies.extend(parse_pom_file(dependency_pom_path, repository_path, processed))
    
    return dependencies



def generate_plantuml_graph(dependencies, output_path):
    with open(output_path, 'w') as file:
        file.write("@startuml\n")
        for dep in dependencies:
            group_id, artifact_id, version = dep.split(":")
            file.write(f'"Root" --> "{group_id}:{artifact_id}:{version}"\n')
        file.write("@enduml\n")
    print(f"Graph saved to {output_path}")

def main():
    # чтение конфигурационного файла
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    pom_path = config["pom_path"]
    output_path = config["output_path"]

    # указание пути к локальному Maven-репозиторию
    repository_path = os.path.expanduser("~/.m2/repository")

    # рекурсивный парсинг зависимостей
    dependencies = parse_pom_file(pom_path, repository_path)

    # генерация графа PlantUML
    generate_plantuml_graph(dependencies, output_path)

    # печать на экран
    with open(output_path, 'r') as file:
        print(file.read())
if __name__ == "__main__":
    main()
