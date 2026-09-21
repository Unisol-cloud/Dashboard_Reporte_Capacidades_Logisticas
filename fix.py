import os

src = r'C:\Users\CQuitral\Documents\Proyecto_Reporteria_Automatica\Reporte_Capacidades_Logisticas\app.py'
dst = r'C:\Users\CQuitral\Documents\Dashboard_Nube\app.py'

with open(src, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('if st.sidebar.button')
end_idx = content.find('# ============================================================', idx)

if idx != -1 and end_idx != -1:
    new_button = 'if st.sidebar.button("🔄 Refrescar Caché", use_container_width=True):\n    st.cache_data.clear()\n    st.success("✅ Caché visual limpia.")\n\n'
    content = content[:idx] + new_button + content[end_idx:]

with open(dst, 'w', encoding='utf-8') as f:
    f.write(content)
