declare module 'ali-oss' {
  interface OSSOptions {
    region: string;
    accessKeyId: string;
    accessKeySecret: string;
    bucket: string;
  }

  interface GetResult {
    content: Buffer;
    res: any;
  }

  interface HeadResult {
    res: {
      headers: Record<string, string>;
      [key: string]: any;
    };
    [key: string]: any;
  }

  interface SignatureUrlOptions {
    expires?: number;
    response?: Record<string, string>;
  }

  class OSS {
    constructor(options: OSSOptions);
    get(key: string): Promise<GetResult>;
    head(key: string): Promise<HeadResult>;
    signatureUrl(key: string, options?: SignatureUrlOptions): string;
  }

  export default OSS;
}
