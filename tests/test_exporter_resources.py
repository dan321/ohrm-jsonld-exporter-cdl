"""Tests for resource exporters."""
from ohrm_converter.exporters.arcresource import export_arcresources
from ohrm_converter.exporters.dobject import export_dobjects
from ohrm_converter.exporters.dobjectversion import export_dobjectversions
from ohrm_converter.exporters.pubresource import export_pubresources
from ohrm_converter.models import ArcResource, DObject, DObjectVersion, PubResource

class TestArcResource:
    def test_basic_export(self):
        rows = [ArcResource(arcid="A001", artitle="Archive One", ardescription="Desc")]
        result = export_arcresources(rows)
        main = [e for e in result if e.get("identifier") == "A001"]
        assert len(main) == 1
        assert main[0]["@type"] == "ArchivalResource"
        assert main[0]["name"] == "Archive One"

class TestDObject:
    def test_basic_export(self):
        rows = [DObject(doid="D001", dotitle="Object One", dotype="Photograph")]
        result = export_dobjects(rows, [])
        main = [e for e in result if e.get("identifier") == "D001"]
        assert len(main) == 1
        assert main[0]["@type"] == ["RepositoryObject", "DigitalObject", "Photograph"]

    def test_links_versions(self):
        rows = [DObject(doid="D001", dotitle="Object One", dotype="Photo")]
        versions = [DObjectVersion(doid="D001", dov="images/photo1.jpg")]
        result = export_dobjects(rows, versions)
        main = [e for e in result if e.get("identifier") == "D001"][0]
        assert len(main["hasFile"]) == 1

    def test_links_archival_resource(self):
        rows = [DObject(doid="D001", dotitle="X", dotype="Y", arcid="A001")]
        result = export_dobjects(rows, [])
        main = [e for e in result if e.get("identifier") == "D001"][0]
        assert main["linkedArchivalResource"] == {"@id": "#A001"}

class TestDObjectVersion:
    def test_basic_export(self):
        rows = [DObjectVersion(doid="D001", dov="images/photo.jpg", dovtype="photograph")]
        result = export_dobjectversions(rows)
        assert len(result) == 1
        assert result[0]["@type"] == ["File", "DigitalObjectVersion", "photograph"]

    def test_multipage_image(self):
        rows = [DObjectVersion(
            doid="D001", dov="path/to/image_viewer_paged.htm?subdir,page1,page2",
            dovtype="multipage image",
        )]
        result = export_dobjectversions(rows)
        main = [e for e in result if "DigitalObjectVersion" in e.get("@type", [])]
        assert len(main) == 1
        assert main[0]["@type"][0] == "Dataset"

    def test_skips_non_viewer_multipage(self):
        rows = [DObjectVersion(doid="D001", dov="plain/path.jpg", dovtype="multipage image")]
        result = export_dobjectversions(rows)
        assert len(result) == 0

    def test_skips_no_dov(self):
        rows = [DObjectVersion(doid="D001")]
        result = export_dobjectversions(rows)
        assert len(result) == 0

class TestPubResource:
    def test_basic_export(self):
        rows = [PubResource(pubid="P001", title="A Paper", type="Journal Article")]
        result = export_pubresources(rows)
        main = [e for e in result if e.get("identifier") == "P001"]
        assert len(main) == 1
        assert "JournalArticle" in main[0]["@type"]

    def test_includes_typeofwork(self):
        rows = [PubResource(pubid="P001", title="X", type="Book", typeofwork="Reference Work")]
        result = export_pubresources(rows)
        main = [e for e in result if e.get("identifier") == "P001"][0]
        assert "PublishedResource" in main["@type"]
        assert "Book" in main["@type"]
        assert "ReferenceWork" in main["@type"]
