// acoBase.hpp
#ifndef ACO_BASE_HPP
#define ACO_BASE_HPP

#include <vector>
#include <string>
#include "problem.hpp"   // define KnapsackProblem

class BaseACO {
public:
    // *** Assinatura idêntica à usada nas variantes (.cpp) ***
    virtual std::vector<int> executar(const KnapsackProblem& problema) = 0;
    virtual std::string getNome() const = 0;
    virtual ~BaseACO() {}
};

#endif
