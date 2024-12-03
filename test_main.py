import unittest
from unittest.mock import patch, mock_open
import os
import tempfile
from main import resolve_property, parse_pom_file, generate_plantuml_graph


class TestDependencyVisualizer(unittest.TestCase):
    def test_resolve_property(self):
        properties = {
            "project.version": "1.0.0",
            "custom.prop": "value123"
        }
        self.assertEqual(resolve_property("${project.version}", properties), "1.0.0")
        self.assertEqual(resolve_property("${custom.prop}", properties), "value123")
        self.assertEqual(resolve_property("${unknown.prop}", properties), "${unknown.prop}")
        self.assertEqual(resolve_property("no_placeholder", properties), "no_placeholder")

    def test_parse_pom_file(self):
        with tempfile.TemporaryDirectory() as repo_dir:
            # тестовый POM-файл
            pom_content = """
                <project xmlns="http://maven.apache.org/POM/4.0.0">
                    <modelVersion>4.0.0</modelVersion>
                    <groupId>com.example</groupId>
                    <artifactId>test-project</artifactId>
                    <version>1.0.0</version>
                    <dependencies>
                        <dependency>
                            <groupId>org.example</groupId>
                            <artifactId>example-lib</artifactId>
                            <version>1.0.1</version>
                        </dependency>
                    </dependencies>
                </project>
            """
            pom_path = os.path.join(repo_dir, "pom.xml")
            with open(pom_path, "w") as pom_file:
                pom_file.write(pom_content)

            # POM для зависимости
            dep_pom_content = """
                <project xmlns="http://maven.apache.org/POM/4.0.0">
                    <modelVersion>4.0.0</modelVersion>
                    <groupId>org.example</groupId>
                    <artifactId>example-lib</artifactId>
                    <version>1.0.1</version>
                </project>
            """
            dep_pom_path = os.path.join(repo_dir, "org", "example", "example-lib", "1.0.1", "example-lib-1.0.1.pom")
            os.makedirs(os.path.dirname(dep_pom_path))
            with open(dep_pom_path, "w") as dep_pom_file:
                dep_pom_file.write(dep_pom_content)

            # запуск тестируемой функции
            graph = parse_pom_file(pom_path, repo_dir)

            # Ппроверка структуры графа
            self.assertIn("com.example:test-project:1.0.0", graph)
            self.assertIn("org.example:example-lib:1.0.1", graph["com.example:test-project:1.0.0"])
            self.assertEqual(len(graph), 2)  # два узла в графе

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_plantuml_graph(self, mock_file):
        graph = {
            "com.example:test-project:1.0.0": ["org.example:example-lib:1.0.1"],
            "org.example:example-lib:1.0.1": []
        }

        # временный файл для вывода
        output_path = "output.puml"
        generate_plantuml_graph(graph, output_path)

        # проверка содержимого сгенерированного файла
        mock_file().write.assert_any_call("@startuml\n")
        mock_file().write.assert_any_call('"com.example:test-project:1.0.0" --> "org.example:example-lib:1.0.1"\n')
        mock_file().write.assert_any_call("@enduml\n")

    def test_integration(self):
        with tempfile.TemporaryDirectory() as repo_dir:
            # создание структуры Maven-репозитория и файлы POM
            pom_path = os.path.join(repo_dir, "pom.xml")
            dep_path = os.path.join(repo_dir, "org/example/example-lib/1.0.1/example-lib-1.0.1.pom")
            os.makedirs(os.path.dirname(dep_path))

            pom_content = """
                <project xmlns="http://maven.apache.org/POM/4.0.0">
                    <groupId>com.example</groupId>
                    <artifactId>test-project</artifactId>
                    <version>1.0.0</version>
                    <dependencies>
                        <dependency>
                            <groupId>org.example</groupId>
                            <artifactId>example-lib</artifactId>
                            <version>1.0.1</version>
                        </dependency>
                    </dependencies>
                </project>
            """
            dep_content = """
                <project xmlns="http://maven.apache.org/POM/4.0.0">
                    <groupId>org.example</groupId>
                    <artifactId>example-lib</artifactId>
                    <version>1.0.1</version>
                </project>
            """

            with open(pom_path, "w") as pom_file:
                pom_file.write(pom_content)
            with open(dep_path, "w") as dep_file:
                dep_file.write(dep_content)

            # генерация графа
            graph = parse_pom_file(pom_path, repo_dir)
            self.assertEqual(len(graph), 2)
            self.assertIn("com.example:test-project:1.0.0", graph)
            self.assertIn("org.example:example-lib:1.0.1", graph["com.example:test-project:1.0.0"])


if __name__ == "__main__":
    unittest.main()
