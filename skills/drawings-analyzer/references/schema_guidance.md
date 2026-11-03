# Schema guidance — designing the DB per discipline

## Universal tables (always)

- `sheets(sheet_id, title, drawing_type, scale, discipline, rev, source_type)`
- `notes(topic, rule_value, source_sheet)` — general/spec notes, one rule per
  row, verbatim value.
- `relationships(from_entity, relation, to_entity, source_sheet, confidence)`
  — connective facts STATED in text.
- `placeholders(entity_or_topic, what_is_missing, why, suggested_sheet)` —
  for facts needing vision (counts off plans, traced runs, raster sheets).

## Entity table (one per discipline)

Keep EVERY listed item even if attributes are null — entity-completeness.

- **Structural**: `footing_schedule`,
  `members(mark, category, section, span_or_location, source_sheet, confidence)`,
  `slabs`, `grids`, `levels`.
- **Plumbing**:
  `fixtures(tag, fixture_class, description, manufacturer, model, schedule_name, source_sheet)`,
  `connections(fixture_tag, service[CW|HW|sewer|trap|vent|gas], size, qty, source_sheet)`,
  `waste_routing(fixture_tag, method, discharges_to, source_sheet)`.
- **Electrical**: `boards(tag, type, rating, voltage, source_sheet)`,
  `circuits(board_tag, circuit_no, load_desc, breaker, cable, source_sheet)`,
  `luminaires(type, description, wattage, ip_rating, mounting, source_sheet)`.
- **HVAC**: `equipment(tag, type, capacity, source_sheet)`,
  `connections(equip_tag, service[supply|return|condensate|gas], size, source_sheet)`.

## Two cross-cutting layers

A/B validated: lifted answers ~9.5→14/16 and calibration ~9→15, well
calibrated, blind-judged.

> Ghi chú: nội dung gốc bị cắt ngay sau dòng này — chưa rõ 2 "cross-cutting
> layers" cụ thể là gì (nhiều khả năng là **reliability score** và
> **context notes**, đã đề cập ở phần "Why both layers" trong SKILL.md, vì
> số liệu A/B ở đây trùng khớp). Nếu anh có phần tiếp theo, gửi thêm để em
> điền chính xác thay vì suy đoán.
