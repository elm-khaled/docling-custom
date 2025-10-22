"""Demonstrates the custom API OCR plugin end-to-end.

The script converts a sample PDF using the custom HTTP OCR service, exports the
resulting document to Markdown, and saves hybrid chunks to disk for inspection.
Enable `allow_external_plugins` and `enable_remote_services` so the HTTP call is
permitted, and set `force_full_page_ocr=True` on the custom OCR options so every
page is processed via OCR.
"""

from __future__ import annotations

from pathlib import Path

from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import CustomApiOcrOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.models.factories import get_ocr_factory


def main():
    project_root = Path(__file__).resolve().parents[2]
    data_folder = project_root / "tests" / "data"
    input_doc_path = data_folder / "pdf" / "2305.03393v1-pg9.pdf"
    input_name = input_doc_path.stem

    pipeline_options = PdfPipelineOptions()
    pipeline_options.enable_remote_services = True
    pipeline_options.allow_external_plugins = True
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.ocr_options = CustomApiOcrOptions(
        url="",
        force_full_page_ocr=True,
    )

    # Confirm that the custom OCR model is registered via the plugin system.
    factory = get_ocr_factory(allow_external_plugins=True)
    meta = factory.registered_meta.get(type(pipeline_options.ocr_options))
    if meta is None:
        # When running from source (without installing the package), entry points might
        # not be picked up automatically. Register manually as a fallback.
        from docling_custom.plugin import register as register_custom_ocr

        factory.process_plugin(
            register_custom_ocr(),
            plugin_name="docling_custom_ocr",
            plugin_module_name="docling_custom.plugin",
        )
        meta = factory.registered_meta.get(type(pipeline_options.ocr_options))
        if meta is None:
            raise RuntimeError("CustomApiOcrModel not registered. Check the plugin setup.")
    print(
        f"Using OCR plugin '{meta.plugin_name}' from module '{meta.module}' with kind "
        f"'{meta.kind}'."
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )

    conv_res = converter.convert(input_doc_path)
    document = conv_res.document

    output_dir = project_root / "artifacts" / "custom_api_ocr"
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = output_dir / f"{input_name}_converted.md"
    markdown_path.write_text(document.export_to_markdown(), encoding="utf-8")
    print(f"Markdown exported to {markdown_path}")

    chunker = HybridChunker()
    chunk_path = output_dir / f"{input_name}_hybrid_chunks.md"
    with chunk_path.open("w", encoding="utf-8") as fh:
        fh.write("# Hybrid chunks\n\n")
        for idx, chunk in enumerate(chunker.chunk(document), start=1):
            contextualized = chunker.contextualize(chunk)
            fh.write(f"## Chunk {idx}\n\n")
            fh.write("**Text**\n\n")
            fh.write("```text\n")
            fh.write(chunk.text.strip() + "\n")
            fh.write("```\n\n")
            fh.write("**Contextualized**\n\n")
            fh.write("```text\n")
            fh.write(contextualized.strip() + "\n")
            fh.write("```\n\n")
            fh.write("---\n\n")
    print(f"Hybrid chunks saved to {chunk_path}")


if __name__ == "__main__":
    main()
