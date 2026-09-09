from process_receipt import extract_vendor_and_total


def make_key_value_blocks(key_text, value_text, key_id, value_id):
    """Build a minimal KEY block and VALUE block pair, linked together,
    the way Textract's real response structures forms data."""
    key_word_id = f"{key_id}-word"
    value_word_id = f"{value_id}-word"

    key_block = {
        "Id": key_id,
        "BlockType": "KEY_VALUE_SET",
        "EntityTypes": ["KEY"],
        "Relationships": [
            {"Type": "CHILD", "Ids": [key_word_id]},
            {"Type": "VALUE", "Ids": [value_id]},
        ],
    }
    value_block = {
        "Id": value_id,
        "BlockType": "KEY_VALUE_SET",
        "EntityTypes": ["VALUE"],
        "Relationships": [
            {"Type": "CHILD", "Ids": [value_word_id]},
        ],
    }
    key_word = {"Id": key_word_id, "BlockType": "WORD", "Text": key_text}
    value_word = {"Id": value_word_id, "BlockType": "WORD", "Text": value_text}

    return [key_block, value_block, key_word, value_word]


def test_extracts_clean_vendor_and_total_from_forms():
    blocks = []
    blocks += make_key_value_blocks("Vendor", "Buffalo", "k1", "v1")
    blocks += make_key_value_blocks("Total", "92.19", "k2", "v2")

    vendor, total = extract_vendor_and_total({"Blocks": blocks})

    assert vendor == "Buffalo"
    assert total == "92.19"


def test_falls_back_to_topmost_line_when_vendor_is_a_store_code():
    blocks = []
    # Forms mode incorrectly tags a store number as "vendor"
    blocks += make_key_value_blocks("Vendor", "#3793", "k1", "v1")
    blocks += make_key_value_blocks("Total", "92.19", "k2", "v2")

    # The real business name appears as a plain LINE block near the top
    blocks.append({
        "Id": "line1",
        "BlockType": "LINE",
        "Text": "Buffalo Wild Wings",
        "Geometry": {"BoundingBox": {"Top": 0.05}},
    })
    blocks.append({
        "Id": "line2",
        "BlockType": "LINE",
        "Text": "Some other line further down",
        "Geometry": {"BoundingBox": {"Top": 0.5}},
    })

    vendor, total = extract_vendor_and_total({"Blocks": blocks})

    assert vendor == "Buffalo Wild Wings"
    assert total == "92.19"