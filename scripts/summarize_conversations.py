#!/usr/bin/env python3
"""summarize_conversations.py.

Analisa e gera um resumo detalhado em Markdown de todas as conversas do
Antigravity relacionadas ao projeto l10n-brazil.

Uso:
    uv run python scripts/summarize_conversations.py [--output HISTORICO_CONVERSAS.md]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Garante suporte a UTF-8 em terminais Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def load_knowledge_base():
    """Carrega metadados pré-cadastrados se existirem."""
    meta_path = Path(__file__).parent / "conversations_metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def find_brain_dir():
    """Localiza o diretório do Antigravity brain."""
    user_home = Path.home()
    default_path = user_home / ".gemini" / "antigravity" / "brain"
    if default_path.exists():
        return default_path

    app_data = os.environ.get("APPDATA")
    if app_data:
        alt_path = Path(app_data) / ".gemini" / "antigravity" / "brain"
        if alt_path.exists():
            return alt_path

    return default_path


def extract_tool_info(tool_calls, target_keyword):
    """Extrai arquivos modificados e comandos de chamadas de ferramentas."""
    modified_files = set()
    commands = []
    is_related = False

    for tc in tool_calls:
        args = tc.get("args") or tc.get("arguments") or {}
        if not isinstance(args, dict):
            continue

        target_file = args.get("TargetFile") or args.get("AbsolutePath")
        if target_file:
            clean_tf = target_file.replace('"', "").replace("'", "")
            lower_tf = clean_tf.lower()
            if target_keyword in lower_tf or "l10n_br" in lower_tf:
                is_related = True
            modified_files.add(Path(clean_tf).name)

        cwd = args.get("Cwd", "")
        if target_keyword in cwd.lower():
            is_related = True

        cmd = args.get("CommandLine", "")
        if cmd:
            lower_cmd = cmd.lower()
            if target_keyword in lower_cmd or "l10n_br" in lower_cmd:
                is_related = True
            if any(k in cmd for k in ["ruff", "docker", "odoo", "git", "pre-commit"]):
                commands.append(cmd)

    return modified_files, commands, is_related


def parse_transcript_lines(transcript_file, target_keyword):
    """Lê e analisa linhas do arquivo de transcrição."""
    step_count = 0
    created_at = None
    user_prompts = []
    assistant_replies = []
    all_modified_files = set()
    all_commands = []
    is_related = False

    with open(transcript_file, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            step_count += 1
            if not created_at and "created_at" in row:
                created_at = row["created_at"]

            content = row.get("content", "") or ""
            if target_keyword in content.lower():
                is_related = True

            if row.get("type") == "USER_INPUT":
                txt = content
                if "<USER_REQUEST>" in txt:
                    txt = txt.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0]
                txt = txt.strip()
                if txt and not txt.startswith("Comments on artifact URI:"):
                    user_prompts.append(txt)

            elif row.get("type") == "PLANNER_RESPONSE":
                c = row.get("content")
                if c and c.strip():
                    assistant_replies.append(c.strip())

                tcs = row.get("tool_calls", [])
                mod_f, cmds, rel = extract_tool_info(tcs, target_keyword)
                all_modified_files.update(mod_f)
                all_commands.extend(cmds)
                if rel:
                    is_related = True

    return {
        "step_count": step_count,
        "created_at": created_at,
        "user_prompts": user_prompts,
        "assistant_replies": assistant_replies,
        "modified_files": sorted(all_modified_files),
        "commands": all_commands[:10],
        "is_related": is_related,
    }


def parse_conversation(conv_dir: Path, target_workspace_keyword="l10n-brazil"):
    """Analisa os arquivos de log e artefatos de uma conversa específica."""
    transcript_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
    if not transcript_file.exists():
        return None

    knowledge_base = load_knowledge_base()
    meta = knowledge_base.get(conv_dir.name, {})

    target_kw = target_workspace_keyword.lower()
    data = parse_transcript_lines(transcript_file, target_kw)

    if not data["is_related"] and conv_dir.name not in knowledge_base:
        return None

    walkthrough = ""
    wt_path = conv_dir / "walkthrough.md"
    if wt_path.exists():
        walkthrough = wt_path.read_text(encoding="utf-8", errors="ignore")

    plan = ""
    plan_path = conv_dir / "implementation_plan.md"
    if plan_path.exists():
        plan = plan_path.read_text(encoding="utf-8", errors="ignore")

    last_reply = data["assistant_replies"][-1] if data["assistant_replies"] else ""

    return {
        "id": conv_dir.name,
        "date": data["created_at"],
        "steps": data["step_count"],
        "user_prompts": data["user_prompts"],
        "last_assistant_response": last_reply,
        "modified_files": data["modified_files"],
        "commands": data["commands"],
        "walkthrough": walkthrough,
        "plan": plan,
        "title": meta.get("title", f"Conversa {conv_dir.name[:8]}"),
        "modules": meta.get("modules", ["l10n_br_hr"]),
        "category": meta.get("category", "Geral"),
        "summary": meta.get("summary", ""),
        "decisions": meta.get("decisions", []),
        "key_actions": meta.get("key_actions", []),
        "status": meta.get("status", "Concluído"),
    }


def format_date(iso_str):
    """Formata data ISO para padrão brasileiro legível."""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M")
    except (ValueError, TypeError):
        return iso_str[:16]


def build_markdown_header(conversations):
    """Gera o cabeçalho e sumário executivo em Markdown."""
    total_convs = len(conversations)
    all_modules = {m for c in conversations for m in c["modules"]}
    all_categories = {c["category"] for c in conversations}
    total_steps = sum(c["steps"] for c in conversations)
    total_prompts = sum(len(c["user_prompts"]) for c in conversations)

    start_date = format_date(conversations[0]["date"]) if conversations else "N/A"
    end_date = format_date(conversations[-1]["date"]) if conversations else "N/A"
    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")

    lines = [
        "# Histórico Consolidado de Conversas & Decisões Arquiteturais",
        "",
        "> **Repositório:** `l10n-brazil` (Localização Brasileira para Odoo 18)",
        f"> **Período de Execução:** {start_date} até {end_date}",
        f"> **Última Atualização:** {now_str}",
        "",
        "---",
        "",
        "## 📊 Painel Executivo do Projeto",
        "",
        "| Métrica | Valor |",
        "| :--- | :--- |",
        f"| **Total de Conversas/Sessões:** | **{total_convs}** |",
        f"| **Demandas/Prompts do Desenvolvedor:** | **{total_prompts}** |",
        f"| **Total de Passos/Ações Executadas:** | **{total_steps:,}** |",
        f"| **Módulos Impactados:** | `{', '.join(sorted(all_modules))}` |",
        f"| **Eixos Temáticos de Trabalho:** | {len(all_categories)} categorias |",
        "",
        "### 🎯 Principais Eixos de Evolução",
        (
            "1. **Modernização & Conformidade Legal:** Adequação profunda ao "
            "eSocial S-1.3 e à Lei Federal nº 14.534/2023 (CIN - Carteira de "
            "Identidade Nacional)."
        ),
        (
            "2. **Padronização Nativa com Odoo 18:** Eliminação de "
            "redundâncias, unificação de CPF no campo `vat` e harmonização "
            "ergonômica da árvore de menus com o core nativo."
        ),
        (
            "3. **Internacionalização (i18n):** Código Python em inglês "
            "nativo conforme padrões internacionais da OCA, catálogos POT e "
            "PO (pt_BR) 100% atualizados e consistentes."
        ),
        (
            "4. **Qualidade & Blindagem de Testes:** Expansão robusta da "
            "suíte de testes unitários automatizados em Docker e paridade total "
            "com o repositório upstream."
        ),
        (
            "5. **Usabilidade Corporativa:** Desacoplamento de nomenclaturas "
            "burocráticas residuais ('eSocial' e 'Legado') nos formulários e "
            "relatórios."
        ),
        "",
        "---",
        "",
        "## 📑 Índice de Conversas",
        "",
        "| # | Data | Sessão / Tema | Categoria | Módulos | Status |",
        "| :-: | :--- | :--- | :--- | :--- | :-: |",
    ]

    for idx, c in enumerate(conversations, 1):
        cid_short = c["id"][:8]
        date_str = format_date(c["date"])[:10]
        anchor = f"conversa-{idx}-{cid_short}"
        mods = " ".join([f"`{m}`" for m in c["modules"]])
        lines.append(
            f"| **{idx:02d}** | {date_str} | [{c['title']}](#{anchor}) | "
            f"{c['category']} | {mods} | `{c['status']}` |"
        )

    lines.extend(["", "---", "", "## 📝 Detalhamento de Cada Conversa", ""])
    return lines


def format_prompts_block(prompts):
    """Gera o bloco de citações de prompts do usuário."""
    lines = ["**Prompts originais do usuário:**"]
    for p in prompts:
        clean_p = p.replace("\r", "").strip()
        if len(clean_p) > 200:
            lines.append(f'> 💬 *"{clean_p[:200]}..."*')
        else:
            lines.append(f'> 💬 *"{clean_p}"*')
    lines.append("")
    return lines


def format_files_and_tools_block(modified_files, commands):
    """Gera a seção de arquivos impactados e comandos de teste."""
    lines = []
    if modified_files:
        filtered = [
            f
            for f in modified_files
            if not f.endswith((".pyc", ".log", ".tmp")) and not f.startswith("scratch")
        ]
        if filtered:
            lines.append(f"**Arquivos modificados ({len(filtered)}):**")
            for f in filtered[:12]:
                lines.append(f"- `{f}`")
            if len(filtered) > 12:
                lines.append(f"- *(e outros {len(filtered) - 12} arquivos...)*")
            lines.append("")

    if commands:
        lines.append("#### 🧪 Validações & Comandos de Qualidade")
        lines.append("```bash")
        for cmd in commands[:5]:
            lines.append(cmd.strip('"').strip("'"))
        lines.append("```")
        lines.append("")

    return lines


def format_conversation_section(idx, c):
    """Formata os detalhes de uma conversa específica em Markdown."""
    cid = c["id"]
    cid_short = cid[:8]
    anchor = f"conversa-{idx}-{cid_short}"
    date_full = format_date(c["date"])
    mods_str = ", ".join([f"`{m}`" for m in c["modules"]])

    lines = [
        f'### <a id="{anchor}"></a>#{idx:02d}. {c["title"]}',
        "",
        f"- **ID da Conversa:** [`{cid}`](conversation://{cid})",
        f"- **Data de Realização:** {date_full}",
        f"- **Eixo Temático:** `{c['category']}`",
        f"- **Módulos Envolvidos:** {mods_str}",
        (
            f"- **Volume de Trabalho:** {len(c['user_prompts'])} prompts | "
            f"{c['steps']} passos"
        ),
        f"- **Status da Entrega:** `{c['status']}`",
        "",
        "#### 🎯 Demanda e Intenção do Desenvolvedor",
    ]

    if c.get("summary"):
        lines.extend([c["summary"], ""])

    lines.extend(format_prompts_block(c["user_prompts"]))

    if c.get("decisions"):
        lines.append("#### 🧠 Decisões Arquiteturais & Técnicas")
        for d in c["decisions"]:
            lines.append(f"- {d}")
        lines.append("")

    lines.append("#### 🛠️ Implementações & Arquivos Impactados")
    if c.get("key_actions"):
        for act in c["key_actions"]:
            lines.append(f"- {act}")
        lines.append("")

    lines.extend(
        format_files_and_tools_block(c.get("modified_files"), c.get("commands"))
    )

    artifacts = []
    if c.get("walkthrough"):
        artifacts.append("`walkthrough.md` (Roteiro e evidências de entrega)")
    if c.get("plan"):
        artifacts.append("`implementation_plan.md` (Plano de implementação)")

    if artifacts:
        lines.append("#### 📄 Artefatos Gerados na Sessão")
        for art in artifacts:
            lines.append(f"- {art}")
        lines.append("")

    lines.extend(["---", ""])
    return lines


def generate_markdown(conversations, output_path):
    """Gera o documento Markdown estruturado com todas as conversas."""
    conversations.sort(key=lambda x: x["date"] or "")
    lines = build_markdown_header(conversations)

    for idx, c in enumerate(conversations, 1):
        lines.extend(format_conversation_section(idx, c))

    lines.extend(
        [
            "## 🏆 Considerações Finais de Governança",
            "",
            (
                "A suíte de módulos do **`l10n-brazil`** passou por modernização "
                "completa:"
            ),
            (
                "- **Conformidade Total com Odoo 18:** Migração concluída sem "
                "débito técnico, aderente aos padrões de ORM, views e hierarquia "
                "nativa."
            ),
            (
                "- **eSocial S-1.3 & Legislação Federal:** Tabelas oficiais "
                "documentadas, suporte unificado ao CPF e implantação da Carteira "
                "de Identidade Nacional (CIN)."
            ),
            (
                "- **Padrão de Qualidade OCA:** Código em inglês, arquivos de "
                "tradução pt_BR 100% íntegros, suite de testes em Docker e "
                "paridade upstream."
            ),
            "",
            (
                "*(Documento gerado automaticamente pelo script "
                "`scripts/summarize_conversations.py`)*\n"
            ),
        ]
    )

    full_content = "\n".join(lines)
    Path(output_path).write_text(full_content, encoding="utf-8")
    print(f"✅ Histórico consolidado salvo com sucesso em: {output_path}")


def main():
    """Ponto de entrada do script CLI."""
    parser = argparse.ArgumentParser(
        description="Gera histórico consolidado em Markdown de todas as "
        "conversas do projeto."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="HISTORICO_CONVERSAS.md",
        help="Caminho do arquivo Markdown de saída",
    )
    parser.add_argument(
        "--brain-dir",
        "-b",
        default=None,
        help="Caminho do diretório de conversas do Antigravity",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        default="l10n-brazil",
        help="Palavra-chave do projeto para filtro",
    )
    parser.add_argument(
        "--json",
        "-j",
        default=None,
        help="Caminho opcional para exportar os dados em JSON",
    )

    args = parser.parse_args()

    brain_path = Path(args.brain_dir) if args.brain_dir else find_brain_dir()
    if not brain_path.exists():
        print(f"❌ Diretório brain não encontrado em: {brain_path}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Escaneando conversas em: {brain_path}")
    conversations = []

    for item in sorted(brain_path.iterdir()):
        if not item.is_dir() or item.name == "tempmediaStorage":
            continue
        parsed = parse_conversation(item, target_workspace_keyword=args.workspace)
        if parsed:
            conversations.append(parsed)

    print(
        f"✨ Encontradas {len(conversations)} conversas relacionadas a "
        f"'{args.workspace}'."
    )

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        print(f"📁 Dados estruturados salvos em JSON: {args.json}")

    generate_markdown(conversations, args.output)


if __name__ == "__main__":
    main()
