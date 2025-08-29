#pragma once
#include <string>
#include <vector>

struct Item {
    long long valor;  // lucro
    long long peso;   // peso
};

class KnapsackProblem {
    std::string nome_;
    long long capacidade_ = 0;
    std::vector<Item> itens_;

public:
    KnapsackProblem() = default;
    explicit KnapsackProblem(const std::string& path) { load(path); }

    // Carrega uma instância do arquivo
    void load(const std::string& path);

    // Getters usados pelo projeto
    const std::vector<Item>& getItens() const { return itens_; }
    long long getCapacidade() const { return capacidade_; }
    const std::string& getNome() const { return nome_; }

    // Funções utilitárias usadas em vários lugares
    long long calcularValor(const std::vector<int>& selecao) const;
    long long calcularPeso (const std::vector<int>& selecao) const;
};
