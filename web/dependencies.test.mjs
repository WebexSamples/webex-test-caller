import { createServer } from "node:http";
import { createRequire } from "node:module";
import { once } from "node:events";
import { describe, expect, it } from "vitest";

const require = createRequire(import.meta.url);

describe("SDK dependency compatibility", () => {
  it("keeps the SDK HTTP client's callback and multipart APIs", async () => {
    const sdkRequire = createRequire(require.resolve("@webex/http-core"));
    const request = sdkRequire("request").defaults({ timeout: 2000, proxy: null });
    const server = createServer(async (req, res) => {
      let body = "";
      for await (const chunk of req) body += chunk;
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ method: req.method, type: req.headers["content-type"], body }));
    });
    server.listen(0, "127.0.0.1");
    await once(server, "listening");
    try {
      const result = await new Promise((resolve, reject) => {
        request.post({
          url: `http://127.0.0.1:${server.address().port}`,
          formData: { phrase: "synthetic speech" },
          json: true,
        }, (error, response, body) => error ? reject(error) : resolve(body));
      });
      expect(result.method).toBe("POST");
      expect(result.type).toMatch(/^multipart\/form-data; boundary=/);
      expect(result.body).toContain('name="phrase"');
      expect(result.body).toContain("synthetic speech");
    } finally {
      await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
    }
  });

  it("preserves named Calling UUIDs and legacy core callable UUIDs", () => {
    const callingRequire = createRequire(require.resolve("@webex/calling"));
    const coreRequire = createRequire(require.resolve("@webex/webex-core"));
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
    expect(callingRequire("uuid").v4()).toMatch(uuidPattern);
    expect(coreRequire("uuid")()).toMatch(uuidPattern);
  });

  it("preserves fingerprint glob and ignore-pattern behavior", async () => {
    const fingerprintRequire = createRequire(require.resolve("@expo/fingerprint"));
    const { glob } = fingerprintRequire("glob");
    const { isIgnoredPath } = require("@expo/fingerprint/build/utils/Path.js");
    expect(await glob("package.json", { cwd: import.meta.dirname, nodir: true })).toEqual(["package.json"]);
    expect(isIgnoredPath("node_modules/sdk/index.js", ["**/node_modules/**"])).toBe(true);
    expect(isIgnoredPath("src/main.ts", ["**/node_modules/**"])).toBe(false);
  });
});
