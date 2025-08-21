// include/problem.hpp
#pragma once
#include <string>
#include <vector>
#include <stdexcept>
#include <cstdint>
#include <algorithm>

struct Item {
    // Nomes canônicos em inglês
    long long value = 0;
    long long weight = 0;
};

// ---------------------------------------------------------------------
// Compatibilidade com código legado: os algoritmos podem usar
// itens[i].valor / itens[i].peso.  Estes macros apenas trocam o token
// por value/weight na hora de compilar.
#define valor value
#define peso  weight
// ---------------------------------------------------------------------

class KnapsackProblem {
public:
    KnapsackProblem() = default;
    explicit KnapsackProblem(const std::string& path) { load(path); }

    void load(const std::string& path);

    const std::string& name() const { return name_; }
    int capacity() const { return capacity_; }
    const std::vector<Item>& items() const { return items_; }

    // Back-compat com código que usa nomes em PT-BR:
    const std::string& getNome()      const { return name_; }
    int                 getCapacidade() const { return capacity_; }
    const std::vector<Item>& getItens() const { return items_; }

    long long calcularValor(const std::vector<int>& sel) const {
        long long v = 0;
        for (size_t i = 0; i < sel.size() && i < items_.size(); ++i) {
            if (sel[i]) v += items_[i].value; // (= itens_[i].valor)
        }
        return v;
    }
    long long calcularPeso(const std::vector<int>& sel) const {
        long long w = 0;
        for (size_t i = 0; i < sel.size() && i < items_.size(); ++i) {
            if (sel[i]) w += items_[i].weight; // (= itens_[i].peso)
        }
        return w;
    }

private:
    std::string name_;
    int capacity_ = 0;
    std::vector<Item> items_;
};
