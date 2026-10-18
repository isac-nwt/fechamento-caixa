import streamlit as st
from datetime import datetime
from typing import List


# ==============================================================================
# CONFIGURAÇÃO VISUAL DA PÁGINA (OTIMIZADA PARA IPHONE / MOBILE)
# ==============================================================================
st.set_page_config(
    page_title="Fechamento de Caixa",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilo CSS customizado para deixar os botões largos e confortáveis para toque no iOS
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# INICIALIZAÇÃO DA MEMÓRIA DO APLICATIVO (SESSION STATE)
# ==============================================================================
if "comandas_almoco" not in st.session_state:
    st.session_state.comandas_almoco = []

if "comandas_jantinha" not in st.session_state:
    st.session_state.comandas_jantinha = []

# Chaves dinâmicas para limpar os campos automaticamente apenas quando o lançamento dá certo
if "form_almoco_id" not in st.session_state:
    st.session_state.form_almoco_id = 0

if "form_jantinha_id" not in st.session_state:
    st.session_state.form_jantinha_id = 0


# ==============================================================================
# REGRA DE NEGÓCIO: AUDITORIA DE INTERVALO DE COMANDAS FALTANTES
# ==============================================================================
def formatar_relatorio_comandas(comandas_registradas: List[int]) -> str:
    """
    Analisa a lista de comandas lançadas no turno, identifica os limites (menor e maior)
    e descobre quais números inteiros intermediários não foram registrados.
    """
    if not comandas_registradas:
        return "nenhuma comanda registrada"

    # 1. Identifica a menor e a maior comanda utilizando min() e max()
    menor_comanda = min(comandas_registradas)
    maior_comanda = max(comandas_registradas)

    # 2. Cria um conjunto (set) com todas as comandas que deveriam existir entre a menor e a maior
    intervalo_esperado = set(range(menor_comanda, maior_comanda + 1))

    # 3. Subtrai as comandas registradas do intervalo completo para achar os furos na sequência
    comandas_ausentes = sorted(list(intervalo_esperado - set(comandas_registradas)))

    # 4. Formata o texto final conforme exigido no relatório
    if not comandas_ausentes:
        return f"da comanda {menor_comanda} a comanda {maior_comanda}, com nenhuma ausência"

    ausentes_str = [str(num) for num in comandas_ausentes]
    if len(ausentes_str) == 1:
        lista_formatada = ausentes_str[0]
    else:
        lista_formatada = ", ".join(ausentes_str[:-1]) + f" e {ausentes_str[-1]}"

    return (
        f"da comanda {menor_comanda} a comanda {maior_comanda}, "
        f"com ausência das comandas {lista_formatada}"
    )


# ==============================================================================
# CABEÇALHO DO APLICATIVO
# ==============================================================================
st.title("📊 Fechamento Diário")
data_selecionada = st.date_input("📅 Data do Fechamento", value=datetime.now(), format="DD/MM/YYYY")
data_formatada = data_selecionada.strftime("%d/%m/%Y")

aba_almoco, aba_jantinha, aba_caixa = st.tabs([
    "☀️ 1. Almoço",
    "🌙 2. Jantinha",
    "💰 3. Caixa e Relatório"
])


# ==============================================================================
# ABA 1: GERENCIAR RESTAURANTE (ALMOÇO)
# ==============================================================================
with aba_almoco:
    st.subheader("Lançar Comanda do Almoço")
    chave_a = st.session_state.form_almoco_id

    col1, col2 = st.columns(2)
    with col1:
        num_cmd_a = st.number_input(
            "Nº da Comanda", min_value=1, step=1, value=None,
            placeholder="Ex: 12", key=f"num_a_{chave_a}"
        )
    with col2:
        val_cmd_a = st.number_input(
            "Valor Total (R$)", min_value=0.0, step=0.50, format="%.2f", value=None,
            placeholder="0.00", key=f"val_a_{chave_a}"
        )

    metodo_a = st.radio(
        "Forma de Pagamento",
        options=["1 - Dinheiro", "2 - Cartão", "3 - Ambos"],
        horizontal=True,
        key=f"met_a_{chave_a}"
    )

    dinheiro_a, cartao_a = 0.0, 0.0
    if metodo_a == "3 - Ambos":
        st.info("Informe abaixo como o valor foi dividido:")
        c_din, c_car = st.columns(2)
        with c_din:
            dinheiro_a = st.number_input(
                "Parte em Dinheiro (R$)", min_value=0.0, step=0.50, format="%.2f",
                value=0.0, key=f"din_a_{chave_a}"
            )
        with c_car:
            cartao_a = st.number_input(
                "Parte no Cartão (R$)", min_value=0.0, step=0.50, format="%.2f",
                value=0.0, key=f"car_a_{chave_a}"
            )

    if st.button("➕ Adicionar Comanda (Almoço)", type="primary"):
        if num_cmd_a is None or val_cmd_a is None or val_cmd_a <= 0:
            st.error("⚠️ Preencha o número da comanda e um valor total maior que zero.")
        else:
            erro_pagamento = False
            if metodo_a == "1 - Dinheiro":
                din_final, car_final = round(val_cmd_a, 2), 0.0
            elif metodo_a == "2 - Cartão":
                din_final, car_final = 0.0, round(val_cmd_a, 2)
            else:
                soma = round(dinheiro_a + cartao_a, 2)
                if abs(soma - val_cmd_a) >= 0.01:
                    st.error(
                        f"⚠️ A soma de Dinheiro + Cartão (R$ {soma:.2f}) não bate "
                        f"com o Valor Total da comanda (R$ {val_cmd_a:.2f})."
                    )
                    erro_pagamento = True
                else:
                    din_final, car_final = round(dinheiro_a, 2), round(cartao_a, 2)

            if not erro_pagamento:
                st.session_state.comandas_almoco.append({
                    "comanda": int(num_cmd_a),
                    "total": round(val_cmd_a, 2),
                    "dinheiro": din_final,
                    "cartao": car_final,
                    "pagamento": metodo_a.split(" - ")[1]
                })
                st.session_state.form_almoco_id += 1
                st.rerun()

    st.divider()
    total_bruto_almoco = round(sum(c["total"] for c in st.session_state.comandas_almoco), 2)
    total_din_almoco = round(sum(c["dinheiro"] for c in st.session_state.comandas_almoco), 2)

    m1, m2, m3 = st.columns(3)
    m1.metric("Qtd. Comandas", len(st.session_state.comandas_almoco))
    m2.metric("Total Almoço", f"R$ {total_bruto_almoco:.2f}")
    m3.metric("Em Dinheiro", f"R$ {total_din_almoco:.2f}")

    if st.session_state.comandas_almoco:
        with st.expander("📋 Ver comandas lançadas no Almoço"):
            st.dataframe(st.session_state.comandas_almoco, use_container_width=True)
            if st.button("↩️ Apagar Última Comanda do Almoço"):
                st.session_state.comandas_almoco.pop()
                st.rerun()


# ==============================================================================
# ABA 2: GERENCIAR JANTINHA (NOITE)
# ==============================================================================
with aba_jantinha:
    st.subheader("📦 Controle de Estoque de Espetos")
    e1, e2, e3 = st.columns(3)
    with e1:
        estoque_ini = st.number_input("Estoque Inicial", min_value=0, step=1, value=0)
    with e2:
        espetos_rep = st.number_input("Chegaram Hoje", min_value=0, step=1, value=0)
    with e3:
        consumo_func = st.number_input("Consumo Func.", min_value=0, step=1, value=0)

    st.divider()
    st.subheader("Lançar Comanda da Jantinha")
    chave_j = st.session_state.form_jantinha_id

    j1, j2, j3 = st.columns(3)
    with j1:
        num_cmd_j = st.number_input(
            "Nº Comanda", min_value=1, step=1, value=None,
            placeholder="Ex: 5", key=f"num_j_{chave_j}"
        )
    with j2:
        espetos_cmd_j = st.number_input(
            "Qtd. Espetos", min_value=0, step=1, value=0,
            key=f"esp_j_{chave_j}"
        )
    with j3:
        val_cmd_j = st.number_input(
            "Valor Total (R$)", min_value=0.0, step=0.50, format="%.2f", value=None,
            placeholder="0.00", key=f"val_j_{chave_j}"
        )

    possui_taxa_j = st.checkbox("✅ Possui taxa de atendimento de 10%?", key=f"tax_j_{chave_j}")

    metodo_j = st.radio(
        "Forma de Pagamento",
        options=["1 - Dinheiro", "2 - Cartão", "3 - Ambos"],
        horizontal=True,
        key=f"met_j_{chave_j}"
    )

    dinheiro_j, cartao_j = 0.0, 0.0
    if metodo_j == "3 - Ambos":
        st.info("Informe abaixo como o valor foi dividido:")
        cj_din, cj_car = st.columns(2)
        with cj_din:
            dinheiro_j = st.number_input(
                "Parte em Dinheiro (R$)", min_value=0.0, step=0.50, format="%.2f",
                value=0.0, key=f"din_j_{chave_j}"
            )
        with cj_car:
            cartao_j = st.number_input(
                "Parte no Cartão (R$)", min_value=0.0, step=0.50, format="%.2f",
                value=0.0, key=f"car_j_{chave_j}"
            )

    if st.button("➕ Adicionar Comanda (Jantinha)", type="primary"):
        if num_cmd_j is None or val_cmd_j is None or val_cmd_j <= 0:
            st.error("⚠️ Preencha o número da comanda e um valor total maior que zero.")
        else:
            erro_pagamento_j = False
            if metodo_j == "1 - Dinheiro":
                din_j_final, car_j_final = round(val_cmd_j, 2), 0.0
            elif metodo_j == "2 - Cartão":
                din_j_final, car_j_final = 0.0, round(val_cmd_j, 2)
            else:
                soma_j = round(dinheiro_j + cartao_j, 2)
                if abs(soma_j - val_cmd_j) >= 0.01:
                    st.error(
                        f"⚠️ A soma de Dinheiro + Cartão (R$ {soma_j:.2f}) não bate "
                        f"com o Valor Total da comanda (R$ {val_cmd_j:.2f})."
                    )
                    erro_pagamento_j = True
                else:
                    din_j_final, car_j_final = round(dinheiro_j, 2), round(cartao_j, 2)

            if not erro_pagamento_j:
                st.session_state.comandas_jantinha.append({
                    "comanda": int(num_cmd_j),
                    "espetos": int(espetos_cmd_j),
                    "total": round(val_cmd_j, 2),
                    "taxa_10": "Sim" if possui_taxa_j else "Não",
                    "dinheiro": din_j_final,
                    "cartao": car_j_final,
                    "pagamento": metodo_j.split(" - ")[1]
                })
                st.session_state.form_jantinha_id += 1
                st.rerun()

    st.divider()
    total_bruto_jantinha = round(sum(c["total"] for c in st.session_state.comandas_jantinha), 2)
    total_din_jantinha = round(sum(c["dinheiro"] for c in st.session_state.comandas_jantinha), 2)
    total_taxa_jantinha = round(
        sum(c["total"] for c in st.session_state.comandas_jantinha if c["taxa_10"] == "Sim"), 2
    )
    espetos_vendidos = sum(c["espetos"] for c in st.session_state.comandas_jantinha)
    estoque_final = (estoque_ini + espetos_rep) - (espetos_vendidos + consumo_func)

    mj1, mj2, mj3 = st.columns(3)
    mj1.metric("Total Jantinha", f"R$ {total_bruto_jantinha:.2f}")
    mj2.metric("Em Dinheiro", f"R$ {total_din_jantinha:.2f}")
    mj3.metric("Freezer Final", f"{estoque_final} esp.")

    if st.session_state.comandas_jantinha:
        with st.expander("📋 Ver comandas lançadas na Jantinha"):
            st.dataframe(st.session_state.comandas_jantinha, use_container_width=True)
            if st.button("↩️ Apagar Última Comanda da Jantinha"):
                st.session_state.comandas_jantinha.pop()
                st.rerun()


# ==============================================================================
# ABA 3: FECHAMENTO FÍSICO DO CAIXA E RELATÓRIO WHATSAPP
# ==============================================================================
with aba_caixa:
    st.subheader("💵 Conferência da Gaveta")

    cx1, cx2 = st.columns(2)
    with cx1:
        caixa_inicial = st.number_input(
            "Caixa Inicial / Abertura (R$)", min_value=0.0, step=5.0, format="%.2f", value=0.0
        )
    with cx2:
        despesas_mercado = st.number_input(
            "Despesas de Mercado (R$)", min_value=0.0, step=5.0, format="%.2f", value=0.0
        )

    entradas_dinheiro = round(total_din_almoco + total_din_jantinha, 2)
    dinheiro_final_caixa = round(caixa_inicial + entradas_dinheiro - despesas_mercado, 2)

    st.metric(
        label="💰 DINHEIRO FINAL ESPERADO NO CAIXA",
        value=f"R$ {dinheiro_final_caixa:.2f}",
        delta=f"Entradas: +R$ {entradas_dinheiro:.2f} | Saídas: -R$ {despesas_mercado:.2f}"
    )

    st.divider()
    st.subheader("📲 Relatório Pronto para WhatsApp")
    st.caption("Toque no ícone de duas folhinhas no canto superior direito do quadro abaixo para copiar tudo:")

    relatorio_cmd_almoco = formatar_relatorio_comandas(
        [c["comanda"] for c in st.session_state.comandas_almoco]
    )
    relatorio_cmd_jantinha = formatar_relatorio_comandas(
        [c["comanda"] for c in st.session_state.comandas_jantinha]
    )

    relatorio_whatsapp = f"""=============================================
RELATÓRIO DIÁRIO DE FECHAMENTO - DIA: {data_formatada}
=============================================
1. RESTAURANTE (ALMOÇO)
- Vendas Totais: R$ {total_bruto_almoco:.2f} (Cartão + Dinheiro)
- Vendas em Dinheiro: R$ {total_din_almoco:.2f}
- Comandas do restaurante: {relatorio_cmd_almoco}

2. JANTINHA (NOITE)
- Vendas Totais: R$ {total_bruto_jantinha:.2f} (Cartão + Dinheiro)
- Vendas em Dinheiro: R$ {total_din_jantinha:.2f}
- Total de vendas com taxa de 10%: R$ {total_taxa_jantinha:.2f}
- Comandas da jantinha: {relatorio_cmd_jantinha}

3. ESTOQUE DE ESPETOS
- Estoque Inicial: {estoque_ini} | Chegaram: {espetos_rep} | Consumo Funcionários: {consumo_func}
- Espetos Vendidos: {espetos_vendidos}
- Estoque Final no Freezer: {estoque_final} espetos

4. FECHAMENTO FÍSICO DO CAIXA
- Caixa Inicial (Abertura): R$ {caixa_inicial:.2f}
- Total Entradas em Dinheiro: R$ {entradas_dinheiro:.2f} (Almoço R$ {total_din_almoco:.2f} + Noite R$ {total_din_jantinha:.2f})
- Despesas de Mercado: R$ {despesas_mercado:.2f}
- DINHEIRO FINAL NO CAIXA: R$ {dinheiro_final_caixa:.2f}
============================================="""

    # O componente st.code gera automaticamente um botão nativo de "Copiar" com 1 toque
    st.code(relatorio_whatsapp, language="text")

    st.divider()
    if st.button("🗑️ Zerar Tudo (Iniciar Novo Dia)"):
        st.session_state.comandas_almoco = []
        st.session_state.comandas_jantinha = []
        st.rerun()