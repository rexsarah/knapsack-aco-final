#ifndef KNAPSACK_PROBLEM_HPP
#define KNAPSACK_PROBLEM_HPP

#include <string>
#include <vector>

struct KPItem {
    int peso;
    long long valor;
};

class KnapsackProblem {
public:
    KnapsackProblem() = default;
    explicit KnapsackProblem(const std::string& filepath) { carregar(filepath); }

    // Carrega instância do arquivo (NMGE e formatos antigos)
    void carregar(const std::string& filepath);

    // Acesso
    const std::vector<KPItem>& getItens() const { return itens; }
    int  getCapacidade() const { return capacidade; }
    const std::string& getNome() const { return nome; }

    // Utilitário: avalia uma seleção 0/1 (mesmo tamanho de itens)
    long long calcularValor(const std::vector<int>& selecao) const;

private:
    std::string nome;
    int capacidade = 0;
    std::vector<KPItem> itens;
};

#endif // KNAPSACK_PROBLEM_HPP
