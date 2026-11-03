# Drawing Type Taxonomy

**Important:** classification is judgement, not pattern matching. Claude
reads the rendered PNG and the vector JSON for each sheet and decides what
type it is. Drawing conventions vary across offices, countries, and
disciplines — there are no reliable regex patterns for sheet numbers.

Use these types and only these types. If a sheet doesn't fit, use `other`
and explain in the justification.

| Type                  | What it is                                                                                    | Common signals                                                                                                                  |
| ---------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `general_arrangement`  | Floor plans, site plans, key plans. The default "layout" sheet. Plan view of a level or area.   | Plan view, scale typically 1:50–1:200, room labels, grid lines, dimensions. No section cuts, no schedules dominating the sheet.     |
| `section_view`         | Vertical cut through the building or a part of it.                                              | Profile geometry, level annotations (FFL, ceiling, roof), labels like "Section 1-1", scale typically 1:50–1:100.                   |
| `elevation`            | External (or internal) view of a vertical surface.                                              | Façade, no floor plan, materials/finishes called out on surfaces, typically 1:50–1:200.                                            |
| `detail`               | Close-up of a specific assembly or junction.                                                    | Scale typically 1:5–1:20, callouts referencing parent sheets, materials labelled with tight specificity.                           |
| `schedule_sheet`       | Tabular data — door, window, ...                                                                | Dominated by tables. Multiple rows × multiple columns. *(bảng gốc bị cắt ở ảnh — cần bổ sung thêm nếu có thêm loại khác, vd. `mep_layout`, `structural_plan`, `other`.)* |

> Ghi chú: nội dung bảng trên được trích lại từ ảnh chụp màn hình và bị cắt
> sau dòng `schedule_sheet`. Nếu anh có thêm các dòng còn lại (các loại khác
> như MEP layout, structural plan...), gửi thêm để em bổ sung đầy đủ bảng.
