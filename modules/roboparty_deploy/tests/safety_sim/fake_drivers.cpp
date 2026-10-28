// SPDX-License-Identifier: GPL-3.0
// Fake motor and IMU drivers for the safety behaviour test. They replace the CAN and serial drivers
// so the real inference node can run without hardware. Every command a motor receives is appended
// to the file named by FAKE_MOTOR_LOG; files in FAKE_TRIGGER_DIR inject faults:
//   tilt  - the IMU reports the robot lying on its side
//   slow  - each IMU read takes 30 ms (forces inference overruns)

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <mutex>
#include <thread>

#include "imu_driver.hpp"
#include "motor_driver.hpp"

namespace {

std::mutex log_mutex;
FILE* log_file() {
    static FILE* f = [] {
        const char* path = std::getenv("FAKE_MOTOR_LOG");
        return path ? std::fopen(path, "w") : nullptr;
    }();
    return f;
}

double now_s() {
    return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}

void log_line(const char* fmt, int id, double a = 0, double b = 0, double c = 0, double d = 0, double e = 0) {
    std::lock_guard<std::mutex> lock(log_mutex);
    if (FILE* f = log_file()) {
        std::fprintf(f, fmt, now_s(), id, a, b, c, d, e);
        std::fflush(f);
    }
}

bool trigger(const char* name) {
    const char* dir = std::getenv("FAKE_TRIGGER_DIR");
    return dir && std::filesystem::exists(std::filesystem::path(dir) / name);
}

class FakeMotor : public MotorDriver {
   public:
    explicit FakeMotor(uint16_t id) { motor_id_ = id; }
    void lock_motor() override { log_line("%.6f,%d,lock,%g,%g,%g,%g,%g\n", motor_id_); }
    void unlock_motor() override { log_line("%.6f,%d,unlock,%g,%g,%g,%g,%g\n", motor_id_); }
    uint8_t init_motor() override {
        log_line("%.6f,%d,init,%g,%g,%g,%g,%g\n", motor_id_);
        return 0;
    }
    void deinit_motor() override { log_line("%.6f,%d,deinit,%g,%g,%g,%g,%g\n", motor_id_); }
    bool set_motor_zero() override { return true; }
    bool write_motor_flash() override { return true; }
    void get_motor_param(uint8_t) override {}
    void motor_pos_cmd(float, float, bool) override {}
    void motor_spd_cmd(float) override {}
    void motor_mit_cmd(float p, float v, float kp, float kd, float t) override {
        log_line("%.6f,%d,mit,%g,%g,%g,%g,%g\n", motor_id_, p, v, kp, kd, t);
        if (kp > 0.0f) {
            motor_pos_.store(p);  // an ideal servo reaches its target
        }
    }
    void motor_mit_cmd(float*, float*, float*, float*, float*) override {}
    void set_motor_control_mode(uint8_t) override {}
    int get_response_count() const override { return 0; }
    void set_motor_id(uint8_t, uint8_t) override {}
    void reset_motor_id() override {}
    void refresh_motor_status() override {}
    void clear_motor_error() override {}
    void set_can_timeout_ms(uint32_t ms) override { log_line("%.6f,%d,timeout,%g,%g,%g,%g,%g\n", motor_id_, ms); }
};

class FakeImu : public IMUDriver {
   public:
    std::vector<float> get_quat() override {
        if (trigger("slow")) {
            std::this_thread::sleep_for(std::chrono::milliseconds(30));
        }
        if (trigger("tilt")) {
            return {0.7071f, 0.7071f, 0.0f, 0.0f};  // rolled 90 degrees
        }
        return {1.0f, 0.0f, 0.0f, 0.0f};
    }
    std::vector<float> get_ang_vel() override { return {0.0f, 0.0f, 0.0f}; }
};

}  // namespace

MotorDriver::MotorDriver() {
    logger_ = spdlog::default_logger();
}

std::shared_ptr<MotorDriver> MotorDriver::create_motor(uint16_t motor_id, const std::string&, const std::string&,
                                                      const std::string&, int, uint16_t, double) {
    return std::make_shared<FakeMotor>(motor_id);
}

std::shared_ptr<IMUDriver> IMUDriver::create_imu(uint16_t, const std::string&, const std::string&,
                                                 const std::string&, const int) {
    return std::make_shared<FakeImu>();
}
