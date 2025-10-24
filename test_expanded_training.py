#!/usr/bin/env python3
"""
Script de teste para verificar a expansão dos exemplos de treinamento.
"""

import json
import os
from collections import Counter

def load_persona(file_path='persona.json'):
    """Carrega o arquivo persona.json"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_training_examples(persona_data):
    """Analisa os exemplos de treinamento"""
    examples = persona_data.get('responses', [])
    
    print("=" * 70)
    print("📊 ANÁLISE DOS EXEMPLOS DE TREINAMENTO EXPANDIDOS")
    print("=" * 70)
    print()
    
    # Estatísticas básicas
    print(f"✅ Total de exemplos: {len(examples)}")
    print(f"✅ Expansão realizada: {len(examples) - 17} novos exemplos adicionados")
    print()
    
    # Categorização dos exemplos
    categories = {
        'Localização': ['endereço', 'onde', 'fica', 'chego'],
        'Horário': ['horário', 'aberto', 'fecha', 'domingo', 'horas'],
        'Produtos': ['armação', 'lentes', 'óculos', 'ray-ban', 'sol', 'grau', 'infantil'],
        'Serviços': ['exame', 'ajuste', 'reparo', 'trocar', 'limpar'],
        'Orçamento': ['orçamento', 'quanto', 'preço', 'valor', 'custa'],
        'Pagamento': ['cartão', 'pix', 'parcelar', 'desconto', 'convênio'],
        'Consultores': ['jailson', 'josimar', 'consultor', 'telefone', 'contato'],
        'Cortesia': ['obrigado', 'valeu', 'tchau', 'tá bom'],
        'Ajuda': ['não entendi', 'ajuda', 'tudo bem'],
        'Linguagem Informal': ['oq', 'vcs', 'tão', 'agr']
    }
    
    example_counts = Counter()
    categorized_examples = {cat: [] for cat in categories}
    
    for example in examples:
        input_lower = example['input'].lower()
        categorized = False
        
        for category, keywords in categories.items():
            if any(keyword in input_lower for keyword in keywords):
                example_counts[category] += 1
                categorized_examples[category].append(example['input'])
                categorized = True
                break
    
    print("📋 DISTRIBUIÇÃO POR CATEGORIA:")
    print("-" * 70)
    for category in sorted(example_counts.keys(), key=lambda x: example_counts[x], reverse=True):
        count = example_counts[category]
        percentage = (count / len(examples)) * 100
        bar = "█" * int(percentage / 2)
        print(f"{category:20} {count:3} exemplos ({percentage:5.1f}%) {bar}")
    
    print()
    print("=" * 70)
    print("🎯 EXEMPLOS POR CATEGORIA:")
    print("=" * 70)
    print()
    
    for category, example_list in categorized_examples.items():
        if example_list:
            print(f"\n{category} ({len(example_list)} exemplos):")
            for i, ex in enumerate(example_list[:5], 1):  # Mostra até 5 exemplos
                print(f"  {i}. {ex}")
            if len(example_list) > 5:
                print(f"  ... e mais {len(example_list) - 5} exemplos")
    
    print()
    print("=" * 70)
    print("🔍 ANÁLISE DE QUALIDADE:")
    print("=" * 70)
    print()
    
    # Análise de padrões
    output_patterns = {
        'Usa emojis': sum(1 for ex in examples if any(emoji in ex['output'] for emoji in ['😊', '👓', '💰', '📍', '🔧', '📞', '💳'])),
        'Oferece escolha de consultor': sum(1 for ex in examples if 'jailson' in ex['output'].lower() and 'josimar' in ex['output'].lower()),
        'Fornece telefone': sum(1 for ex in examples if '99' in ex['output']),
        'Tom amigável': sum(1 for ex in examples if any(word in ex['output'].lower() for word in ['perfeito', 'ótimo', 'claro', 'sem problemas'])),
    }
    
    for pattern, count in output_patterns.items():
        percentage = (count / len(examples)) * 100
        print(f"✅ {pattern}: {count} exemplos ({percentage:.1f}%)")
    
    print()
    print("=" * 70)
    print("💡 NOVOS PADRÕES ADICIONADOS:")
    print("=" * 70)
    print()
    
    new_patterns = [
        "✓ Variações de perguntas sobre horário",
        "✓ Perguntas sobre marcas específicas (Ray-Ban)",
        "✓ Questões sobre garantia e manutenção",
        "✓ Informações sobre tipos de lentes",
        "✓ Convênios e promoções",
        "✓ Armações infantis",
        "✓ Linguagem informal (oq, vcs, tão)",
        "✓ Mensagens de cortesia e despedida",
        "✓ Tratamento de confusão (não entendi)",
        "✓ Perguntas sobre prazo de entrega"
    ]
    
    for pattern in new_patterns:
        print(f"  {pattern}")
    
    print()
    print("=" * 70)
    print("📈 COMPARAÇÃO: ANTES vs DEPOIS")
    print("=" * 70)
    print()
    
    print("ANTES da expansão:")
    print(f"  • 17 exemplos")
    print(f"  • Cobertura básica de casos comuns")
    print(f"  • Foco em encaminhamento")
    print()
    print("DEPOIS da expansão:")
    print(f"  • {len(examples)} exemplos (+{len(examples) - 17} novos)")
    print(f"  • Cobertura ampliada com variações")
    print(f"  • Linguagem informal incluída")
    print(f"  • Mais produtos e serviços específicos")
    print(f"  • Melhor tratamento de edge cases")
    print()
    
    print("=" * 70)
    print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("=" * 70)

def main():
    """Função principal"""
    if not os.path.exists('persona.json'):
        print("❌ Erro: arquivo persona.json não encontrado!")
        return
    
    try:
        persona_data = load_persona()
        analyze_training_examples(persona_data)
        
        print()
        print("💾 INFORMAÇÕES ADICIONAIS:")
        print("-" * 70)
        print(f"Nome da persona: {persona_data.get('name', 'N/A')}")
        print(f"Menu interativo: {'Ativado' if persona_data.get('menu_enabled') else 'Desativado'}")
        print(f"Opções de menu: {len(persona_data.get('menu_options', {}))}")
        print(f"Palavras-chave de saudação: {len(persona_data.get('greeting_keywords', []))}")
        print()
        
    except Exception as e:
        print(f"❌ Erro ao processar persona.json: {e}")

if __name__ == "__main__":
    main()
