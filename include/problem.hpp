#pragma once
#include <string>
#include <vector>
#include <stdexcept>

// Mantém os nomes que suas variantes já usam:
struct Item {
    int valor;
    int peso;
};

class KnapsackProblem {
public:
    KnapsackProblem() = default;
    explicit KnapsackProblem(const std::string& filepath) { carregar(filepath); }

    void carregar(const std::string& filepath);

    // Assinaturas esperadas pelas variantes:
    const std::vector<Item>& getItens() const { return itens; }
    int getCapacidade() const { return capacidade; }
    int calcularValor(const std::vector<int>& selecao) const;

    // Conveniência: usa nome do arquivo como nome lógico (p01, p02,...)
    const std::string& getNome() const { return nome; }

private:
    std::string nome;          // ex.: "p01"
    int capacidade = 0;
    std::vector<Item> itens;
};
