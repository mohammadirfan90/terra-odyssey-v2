import nextConfig from "eslint-config-next";

export default [
  ...nextConfig,
  {
    ignores: [".next/*", "out/*", "node_modules/*", "next-env.d.ts"],
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "import/no-anonymous-default-export": "off",
    },
  },
];
