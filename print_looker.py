import json
import os
import time
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES ---
REPORT_URL = "https://lookerstudio.google.com/s/mi_KNAkqTZc" 
# ---------------------

def run():
    print("--- Iniciando Print via Bounding Box (Detecção Automática) ---")
    
    auth_json = os.environ.get("LOOKER_COOKIES")
    if not auth_json:
        raise ValueError("ERRO: O segredo LOOKER_COOKIES não foi encontrado!")

    state = json.loads(auth_json)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Viewport GIGANTE para garantir que o Looker renderize tudo
        # Isso não afeta o tamanho do print final (que será recortado),
        # mas garante que o rodapé não fique branco.
        context = browser.new_context(
            storage_state=state,
            viewport={'width': 2200, 'height': 4000},
            device_scale_factor=1
        )
        
        page = context.new_page()
        page.set_default_timeout(120000)
        
        print(f"Acessando: {REPORT_URL}")
        page.goto(REPORT_URL)
        
        # Aguarda a div principal aparecer
        try:
            page.wait_for_selector(".ng2-canvas-container", state="visible", timeout=60000)
            print("Container do relatório carregado.")
        except:
            print("Aviso: Timeout esperando seletor, tentando prosseguir...")

        # Espera extra para gráficos
        time.sleep(20)

        # --- FASE 1: REFRESH ---
        try:
            print("Verificando necessidade de refresh...")
            edit_btn = page.get_by_role("button", name="Editar", exact=True).or_(page.get_by_role("button", name="Edit", exact=True))
            if edit_btn.count() > 0 and edit_btn.first.is_visible():
                edit_btn.first.click()
                print("> Refresh: Entrou no Modo Edição...")
                time.sleep(15)
                
                leitura_btn = page.get_by_role("button", name="Leitura").or_(page.get_by_text("Leitura"))
                if leitura_btn.count() > 0:
                    leitura_btn.first.click()
                    print("> Refresh: Voltou para Leitura...")
                    time.sleep(15)
        except Exception as e:
            print(f"Erro no ciclo de refresh: {e}")

        # --- FASE 2: LIMPEZA VISUAL (Opcional, mas ajuda) ---
        # Mesmo usando Bounding Box, esconder o cabeçalho dá mais espaço na tela
        print("Tentando limpar interface via CSS...")
        try:
            page.evaluate("""() => {
                // Remove cabeçalhos, barras de navegação e rodapés
                const selectors = [
                    'header', 
                    '.lego-report-header', 
                    '.page-navigation-panel', // Barra de abas (Fechamento/FIFO...)
                    '#align-lens-view',
                    '.feature-content-header'
                ];
                selectors.forEach(s => {
                    let els = document.querySelectorAll(s);
                    els.forEach(e => e.style.display = 'none');
                });
                // Remove margens do body
                document.body.style.margin = '0';
                document.body.style.padding = '0';
            }""")
            time.sleep(2)
        except Exception as e:
            print(f"Erro ao injetar CSS (não crítico): {e}")

        # --- FASE 3: DETECÇÃO E RECORTE AUTOMÁTICO ---
        print("Calculando coordenadas exatas da div .ng2-canvas-container...")
        
        # Localiza o elemento
        report_element = page.locator(".ng2-canvas-container").first
        
        # Obtém a caixa delimitadora (x, y, width, height) reais na tela
        box = report_element.bounding_box()
        
        if box:
            print(f"Div encontrada em: X={box['x']}, Y={box['y']}, Largura={box['width']}, Altura={box['height']}")
            
            # Tira o print usando o 'clip' com as coordenadas EXATAS do elemento
            # Isso recorta perfeitamente, ignorando se tem cabeçalho em cima ou não.
            page.screenshot(
                path="looker_evidence.png",
                clip=box
            )
            print("Sucesso! Imagem salva recortada exatamente na div.")
        else:
            print("ERRO CRÍTICO: Não consegui calcular o tamanho da div. Tirando print da tela toda.")
            page.screenshot(path="looker_evidence_full.png", full_page=True)

        browser.close()

if __name__ == "__main__":
    run()
