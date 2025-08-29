#pragma once
#include <cstddef>
#include <string>
#include <unordered_map>

/**
 * Perfil 1 (baseline robusto para 0-1 Knapsack)
 *  - alpha = 1.0, beta = 3.0, rho = 0.20
 *  - ants = 30, iterations = 250, seed = 42
 *  - AS: Q=1.0
 *  - ASRank: ranks=10, w_elite=10, Q=1.0
 *  - MMAS: tau_max0=0.50, tau_min0=0.10*tau_max0, clamp_after_each_update=true
 *  - ACS: q0=0.90, xi=0.10, tau0=0.01
 */

struct CommonParams {
    double alpha = 1.0;
    double beta  = 3.0;
    double rho   = 0.20;
    int ants     = 30;
    int iterations = 250;
    unsigned int seed = 42;
};

struct ASParams {
    double Q = 1.0;
};

struct ASRankParams {
    int ranks = 10;
    int elite_weight = 10;
    double Q = 1.0;
};

struct MMASParams {
    double tau_max0 = 0.50;
    double tau_min0 = 0.05;              // atualizado nos perfis para 0.10*tau_max0
    bool clamp_after_each_update = true;
};

struct ACSParams {
    double q0  = 0.90;
    double xi  = 0.10;
    double tau0 = 0.01;
};

struct Profile {
    std::string name = "perfil1";
    CommonParams common;
    ASParams     as;
    ASRankParams asrank;
    MMASParams   mmas;
    ACSParams    acs;
};

// ---------- Perfil 1 ----------
inline Profile get_profile1() {
    Profile p;
    p.name = "perfil1";
    // mantém os defaults do struct; só garante a razão de MMAS:
    p.mmas.tau_min0 = 0.10 * p.mmas.tau_max0;
    return p;
}

/**
 * Perfil 2 (variação mais “exploratória”)
 *  - Mais formigas e beta maior; evaporação menor.
 *  - ASRank com elite maior; ACS com q0 menor (menos determinístico) e xi menor.
 *  - Mantém MESMA quantidade/ordem de campos do Perfil 1.
 */
inline Profile get_profile2() {
    Profile p;
    p.name = "perfil2";

    // Common
    p.common.alpha = 1.0;
    p.common.beta  = 4.0;
    p.common.rho   = 0.10;
    p.common.ants  = 40;
    p.common.iterations = 250;
    p.common.seed  = 1337;

    // AS
    p.as.Q = 1.0;

    // ASRank
    p.asrank.ranks = 10;
    p.asrank.elite_weight = 15;
    p.asrank.Q = 1.0;

    // MMAS
    p.mmas.tau_max0 = 0.60;
    p.mmas.tau_min0 = 0.10 * p.mmas.tau_max0;
    p.mmas.clamp_after_each_update = true;

    // ACS
    p.acs.q0  = 0.85;
    p.acs.xi  = 0.05;
    p.acs.tau0 = 0.01;

    return p;
}

/**
 * Perfil 3 (mais “agressivo” / intensificação)
 *  - Mais formigas e iterações; beta um pouco menor; evaporação menor.
 *  - ASRank com elite mais forte; ACS mais exploratório (q0 menor).
 *  - Mantém MESMA estrutura de campos dos perfis anteriores.
 */
inline Profile get_profile3() {
    Profile p;
    p.name = "perfil3";

    // Common
    p.common.alpha = 1.0;
    p.common.beta  = 2.5;
    p.common.rho   = 0.05;
    p.common.ants  = 50;
    p.common.iterations = 300;
    p.common.seed  = 2025;

    // AS
    p.as.Q = 1.0;

    // ASRank
    p.asrank.ranks = 10;
    p.asrank.elite_weight = 20;
    p.asrank.Q = 1.0;

    // MMAS
    p.mmas.tau_max0 = 0.70;
    p.mmas.tau_min0 = 0.10 * p.mmas.tau_max0;
    p.mmas.clamp_after_each_update = true;

    // ACS
    p.acs.q0  = 0.80;
    p.acs.xi  = 0.05;
    p.acs.tau0 = 0.01;

    return p;
}

// ---------- Registro para a CLI ----------
inline std::unordered_map<std::string, Profile> get_profiles() {
    return {
        {"1",       get_profile1()},
        {"perfil1", get_profile1()},
        {"2",       get_profile2()},
        {"perfil2", get_profile2()},
        {"3",       get_profile3()},
        {"perfil3", get_profile3()}
    };
}
