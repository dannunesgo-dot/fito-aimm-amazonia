(function () {
  function byId(id) {
    return document.getElementById(id);
  }

  function v(id) {
    const el = byId(id);
    return el ? String(el.value || "").trim() : "";
  }

  function gerarInstrucao() {
    const data = {
      case_id: v("case_id"),
      codigo_ibge: v("codigo_ibge"),
      municipio: v("municipio"),
      uf: v("uf").toUpperCase(),
      area_km2: v("area_km2"),
      drive_input_folder: v("drive_input_folder"),
      objetivo: v("objetivo"),
      tipo_projeto: v("tipo_projeto"),
      nivel_relatorio: v("nivel_relatorio"),
      observacao: v("observacao")
    };

    const out = [
      "RODADA 4.37 — DADOS PARA EXECUÇÃO",
      "",
      `case_id: ${data.case_id}`,
      `codigo_ibge: ${data.codigo_ibge}`,
      `municipio: ${data.municipio}`,
      `uf: ${data.uf}`,
      `area_km2: ${data.area_km2}`,
      `drive_input_folder: ${data.drive_input_folder}`,
      `objetivo_projeto: ${data.objetivo}`,
      `tipo_projeto: ${data.tipo_projeto}`,
      `nivel_relatorio: ${data.nivel_relatorio}`,
      "usar_gis: sim",
      "extrair_documentos: sim",
      `observacao: ${data.observacao}`,
      "",
      "Abra o workflow:",
      "https://github.com/dannunesgo-dot/fito-aimm-amazonia/actions/workflows/rodada_4_37_operational_interface_inputs.yml",
      "",
      "Copie cada valor para o campo correspondente e execute Run workflow."
    ].join("\n");

    byId("saida").textContent = out;
  }

  document.addEventListener("DOMContentLoaded", function () {
    const btn = byId("btn-gerar");
    if (btn) btn.addEventListener("click", gerarInstrucao);
  });

  window.gerarInstrucao = gerarInstrucao;
})();