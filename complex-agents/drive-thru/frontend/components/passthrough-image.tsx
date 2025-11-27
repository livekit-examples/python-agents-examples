'use client';

import Image, { type ImageLoader, type ImageProps } from 'next/image';

const passthroughImageLoader: ImageLoader = ({ src }) => src;

type PassthroughImageProps = Omit<ImageProps, 'loader' | 'unoptimized'>;

export function PassthroughImage({ alt, ...props }: PassthroughImageProps) {
  return <Image alt={alt} loader={passthroughImageLoader} unoptimized {...props} />;
}
