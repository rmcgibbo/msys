#include "sdf.hxx"

using namespace desres::msys;

int main(int argc, char *argv[]) {
    for (int i=1; i<argc; i++) {
        auto scanner = ScanSdf(argv[i]);
        for (;;) {
            auto ptr = scanner->next();
            if (!ptr) break;
#if 0
            try {
                ptr->data().at("TAUTOMER_DISTRIBUTION");
            }
            catch (std::exception& e) {
                printf("failed: %s\n", e.what());
                break;
            }
#endif
        }
    }
    return 0;
}